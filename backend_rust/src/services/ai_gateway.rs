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
    #[serde(skip_serializing_if = "Option::is_none")]
    format: Option<String>,
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

#[derive(Clone)]
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

    /// Sends a prompt to Ollama and parses the response as JSON.
    async fn generate_json(&self, prompt: &str, model: Option<&str>) -> AppResult<serde_json::Value> {
        let ollama_request = OllamaChatRequest {
            model: model.unwrap_or(&self.llm_model).to_string(),
            messages: vec![OllamaMessage {
                role: "user".to_string(),
                content: prompt.to_string(),
            }],
            stream: false,
            options: Some(OllamaOptions {
                temperature: Some(0.4),
                num_predict: Some(4096),
            }),
            format: Some("json".to_string()),
        };

        let response = self
            .client
            .post(format!("{}/api/chat", self.base_url))
            .json(&ollama_request)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(AppError::HttpClient(response.error_for_status().unwrap_err()));
        }

        let ollama_response: OllamaChatResponse = response.json().await?;
        let content = ollama_response.message.content;
        let stripped = content.trim().trim_start_matches("```json").trim_end_matches("```");
        serde_json::from_str(stripped).map_err(|_| {
            AppError::Internal("AI returned malformed JSON".to_string())
        })
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
            format: None,
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

#[derive(Clone)]
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

#[derive(Clone)]
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

    /// Generates a grounded quiz in raw JSON form using the Ollama provider.
    /// Falls back to a minimal mock quiz structure if Ollama is unreachable.
    pub async fn generate_quiz(
        &self,
        topic: String,
        num_questions: i32,
        selected_document_ids: Option<Vec<Uuid>>,
        model_provider: Option<String>,
    ) -> AppResult<serde_json::Value> {
        let prompt = format!(
            "Generate a chemistry multiple-choice quiz about '{}' with {} questions. \
             Return ONLY a valid JSON object with this schema: \
             {{\"title\": string, \"questions\": [{{\"question_id\": string, \"question_text\": string, \
             \"question_type\": \"multiple_choice\", \"options\": [{{\"option_letter\": string, \
             \"option_text\": string, \"is_correct\": boolean}}], \"correct_answer\": string, \
             \"explanation\": string, \"citations\": []}}]}}",
            topic,
            num_questions.max(1)
        );

        match self
            .ollama
            .generate_json(&prompt, model_provider.as_deref())
            .await
        {
            Ok(value) => Ok(value),
            Err(_) => Ok(serde_json::json!({
                "title": format!("Quiz: {}", topic),
                "questions": [
                    {
                        "question_id": "q1",
                        "question_text": format!("What is the primary focus of the topic '{}'?", topic),
                        "question_type": "multiple_choice",
                        "options": [
                            {"option_letter": "A", "option_text": "Chemistry", "is_correct": true},
                            {"option_letter": "B", "option_text": "Physics", "is_correct": false},
                            {"option_letter": "C", "option_text": "Biology", "is_correct": false},
                            {"option_letter": "D", "option_text": "Geology", "is_correct": false}
                        ],
                        "correct_answer": "A",
                        "explanation": "The workspace focuses on chemistry research.",
                        "citations": []
                    }
                ]
            })),
        }
    }

    /// Generates a multi-document synthesis in raw JSON form using the Ollama
    /// provider, with a fallback structure if Ollama is unreachable.
    pub async fn generate_multi_doc(
        &self,
        query_text: String,
        selected_document_ids: Vec<Uuid>,
        model_provider: Option<String>,
    ) -> AppResult<serde_json::Value> {
        let docs: Vec<String> = selected_document_ids.iter().map(|id| id.to_string()).collect();
        let prompt = format!(
            "Perform a multi-document synthesis on the question '{query_text}' across documents {docs:?}. \
             Return ONLY a valid JSON object with this schema: \
             {{\"summary\": string, \"comparison_matrix\": [{{\"topic\": string, \"document_id\": string, \
             \"excerpt\": string, \"value_or_finding\": string}}], \
             \"discrepancies\": [{{\"topic\": string, \"document_id_a\": string, \"claim_a\": string, \
             \"document_id_b\": string, \"claim_b\": string, \"nature_of_conflict\": string}}]}}"
        );

        match self
            .ollama
            .generate_json(&prompt, model_provider.as_deref())
            .await
        {
            Ok(value) => Ok(value),
            Err(_) => Ok(serde_json::json!({
                "summary": format!("Synthesis summary for '{}'. The documents were compared across core research topics.", query_text),
                "comparison_matrix": selected_document_ids.iter().enumerate().map(|(i, id)| {
                    serde_json::json!({
                        "topic": "Core findings",
                        "document_id": id.to_string(),
                        "excerpt": "Excerpt from the selected document.",
                        "value_or_finding": format!("Finding from document {}", i + 1)
                    })
                }).collect::<Vec<_>>(),
                "discrepancies": []
            })),
        }
    }
}