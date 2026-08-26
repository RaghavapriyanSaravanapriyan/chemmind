use async_trait::async_trait;
use futures::stream::{self, StreamExt};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::time::Duration;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::models::conversation::{CitationResponse, CreateCitation};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIChatRequest {
    pub prompt: String,
    pub selected_document_ids: Option<Vec<Uuid>>,
    pub model_provider: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIChatResponse {
    pub message_id: Uuid,
    pub sender: String,
    pub content: String,
    pub citations: Vec<CitationResponse>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIChatStreamChunk {
    pub token: String,
    pub finish_reason: Option<String>,
    pub citations: Option<Vec<CreateCitation>>,
    pub full_content: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OllamaChatRequest {
    model: String,
    messages: Vec<OllamaMessage>,
    stream: bool,
    options: Option<OllamaOptions>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OllamaMessage {
    role: String,
    content: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OllamaOptions {
    temperature: Option<f32>,
    num_predict: Option<i32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OllamaChatResponse {
    model: String,
    message: OllamaMessage,
    done: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OllamaEmbedRequest {
    model: String,
    input: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OllamaEmbedResponse {
    embeddings: Vec<Vec<f32>>,
}

#[async_trait]
pub trait LLMProvider: Send + Sync {
    async fn generate(&self, request: AIChatRequest) -> AppResult<(String, Vec<CreateCitation>)>;
    async fn stream(&self, request: AIChatRequest) -> AppResult<Vec<AIChatStreamChunk>>;
    async fn embed(&self, texts: Vec<String>) -> AppResult<Vec<Vec<f32>>>;
}

pub struct OllamaProvider {
    client: Client,
    base_url: String,
    llm_model: String,
    embedding_model: String,
}

impl OllamaProvider {
    pub fn new(settings: &Settings) -> Self {
        Self {
            client: Client::builder()
                .timeout(Duration::from_secs(120))
                .build()
                .expect("Failed to create HTTP client"),
            base_url: settings.ollama_base_url.clone(),
            llm_model: settings.default_llm_model.clone(),
            embedding_model: settings.default_embedding_model.clone(),
        }
    }

    fn build_prompt(&self, request: &AIChatRequest) -> String {
        let doc_context = if let Some(doc_ids) = &request.selected_document_ids {
            format!("\n\nContext documents: {}", doc_ids.iter().map(|id| id.to_string()).collect::<Vec<_>>().join(", "))
        } else {
            String::new()
        };

        format!(
            "You are ChemMind, an AI assistant for chemistry research. Answer the user's question based on the provided context.{}\n\nQuestion: {}",
            doc_context, request.prompt
        )
    }
}

#[async_trait]
impl LLMProvider for OllamaProvider {
    async fn generate(&self, request: AIChatRequest) -> AppResult<(String, Vec<CreateCitation>)> {
        let prompt = self.build_prompt(&request);
        let model = request.model_provider.as_deref().unwrap_or(&self.llm_model);

        let ollama_request = OllamaChatRequest {
            model: model.to_string(),
            messages: vec![OllamaMessage {
                role: "user".to_string(),
                content: prompt,
            }],
            stream: false,
            options: Some(OllamaOptions {
                temperature: Some(0.7),
                num_predict: Some(2048),
            }),
        };

        let response = self
            .client
            .post(format!("{}/api/chat", self.base_url))
            .json(&ollama_request)
            .send()
            .await?;

        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_default();
            return Err(AppError::HttpClient(reqwest::Error::from(response.error_for_status().unwrap_err())));
        }

        let ollama_response: OllamaChatResponse = response.json().await?;
        let answer = ollama_response.message.content;

        // Generate mock citations for now
        let citations = if let Some(doc_ids) = request.selected_document_ids {
            doc_ids.into_iter().map(|doc_id| CreateCitation {
                document_id: Some(doc_id),
                page: Some(1),
                chunk_id: Some("chunk-001".to_string()),
                section: Some("Introduction".to_string()),
                excerpt: Some(format!("Evidence for: {}", request.prompt.chars().take(50).collect::<String>())),
            }).collect()
        } else {
            vec![]
        };

        Ok((answer, citations))
    }

    async fn stream(&self, request: AIChatRequest) -> AppResult<Vec<AIChatStreamChunk>> {
        let (answer, citations) = self.generate(request.clone()).await?;
        
        // Split into words for simulated streaming
        let words: Vec<&str> = answer.split_whitespace().collect();
        let mut chunks = Vec::new();
        let mut accumulated = String::new();

        for (i, word) in words.iter().enumerate() {
            let token = if i < words.len() - 1 {
                format!("{} ", word)
            } else {
                word.to_string()
            };
            accumulated.push_str(&token);
            chunks.push(AIChatStreamChunk {
                token,
                finish_reason: None,
                citations: None,
                full_content: None,
            });
        }

        // Final chunk with citations
        chunks.push(AIChatStreamChunk {
            token: String::new(),
            finish_reason: Some("stop".to_string()),
            citations: Some(citations),
            full_content: Some(accumulated),
        });

        Ok(chunks)
    }

    async fn embed(&self, texts: Vec<String>) -> AppResult<Vec<Vec<f32>>> {
        let request = OllamaEmbedRequest {
            model: self.embedding_model.clone(),
            input: texts,
        };

        let response = self
            .client
            .post(format!("{}/api/embed", self.base_url))
            .json(&request)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(AppError::HttpClient(response.error_for_status().unwrap_err()));
        }

        let embed_response: OllamaEmbedResponse = response.json().await?;
        Ok(embed_response.embeddings)
    }
}

pub struct MockProvider;

#[async_trait]
impl LLMProvider for MockProvider {
    async fn generate(&self, request: AIChatRequest) -> AppResult<(String, Vec<CreateCitation>)> {
        let doc_id = request.selected_document_ids.and_then(|ids| ids.into_iter().next());
        let answer = format!(
            "ChemMind AI [mock]: Grounded analysis for '{}'. Based on scientific sources in workspace.",
            request.prompt
        );

        let citations = if let Some(doc_id) = doc_id {
            vec![CreateCitation {
                document_id: Some(doc_id),
                page: Some(1),
                chunk_id: Some("chunk-001".to_string()),
                section: Some("Introduction & Experimental Methods".to_string()),
                excerpt: Some(format!("Extracted evidence corresponding to user query: {}...", request.prompt.chars().take(40).collect::<String>())),
            }]
        } else {
            vec![]
        };

        Ok((answer, citations))
    }

    async fn stream(&self, request: AIChatRequest) -> AppResult<Vec<AIChatStreamChunk>> {
        let (answer, citations) = self.generate(request).await?;
        let words: Vec<&str> = answer.split_whitespace().collect();
        let mut chunks = Vec::new();
        let mut accumulated = String::new();

        for (i, word) in words.iter().enumerate() {
            let token = if i < words.len() - 1 {
                format!("{} ", word)
            } else {
                word.to_string()
            };
            accumulated.push_str(&token);
            chunks.push(AIChatStreamChunk {
                token,
                finish_reason: None,
                citations: None,
                full_content: None,
            });
        }

        chunks.push(AIChatStreamChunk {
            token: String::new(),
            finish_reason: Some("stop".to_string()),
            citations: Some(citations),
            full_content: Some(accumulated),
        });

        Ok(chunks)
    }

    async fn embed(&self, texts: Vec<String>) -> AppResult<Vec<Vec<f32>>> {
        // Return mock embeddings (384 dimensions)
        Ok(texts.iter().map(|_| vec![0.1; 384]).collect())
    }
}

pub struct AIGateway {
    ollama: OllamaProvider,
    mock: MockProvider,
}

impl AIGateway {
    pub fn new(settings: &Settings) -> Self {
        Self {
            ollama: OllamaProvider::new(settings),
            mock: MockProvider,
        }
    }

    pub async fn generate_rag_response(
        &self,
        request: AIChatRequest,
    ) -> AppResult<(String, Vec<CreateCitation>)> {
        let provider_name = request.model_provider.as_deref().unwrap_or("ollama");
        
        match provider_name {
            "ollama" => self.ollama.generate(request).await,
            "mock" => self.mock.generate(request).await,
            _ => self.mock.generate(request).await, // fallback
        }
    }

    pub async fn stream_rag_response(
        &self,
        request: AIChatRequest,
    ) -> AppResult<Vec<AIChatStreamChunk>> {
        let provider_name = request.model_provider.as_deref().unwrap_or("ollama");
        
        match provider_name {
            "ollama" => self.ollama.stream(request).await,
            "mock" => self.mock.stream(request).await,
            _ => self.mock.stream(request).await, // fallback
        }
    }

    pub async fn embed(&self, texts: Vec<String>, provider: Option<&str>) -> AppResult<Vec<Vec<f32>>> {
        match provider.unwrap_or("ollama") {
            "ollama" => self.ollama.embed(texts).await,
            "mock" => self.mock.embed(texts).await,
            _ => self.mock.embed(texts).await,
        }
    }
}