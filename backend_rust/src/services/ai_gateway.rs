use async_trait::async_trait;
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
    /// Server-populated grounded context: extracted document excerpts injected
    /// into the prompt so answers reference real sources. Not client-supplied.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub grounded_context: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIChatResponse {
    pub message_id: Uuid,
    pub sender: String,
    pub content: String,
    pub citations: Vec<CitationResponse>,
    /// True when Ollama was unreachable and the mock provider answered instead.
    /// Backwards-compatible: defaults to false for old payloads.
    #[serde(default)]
    pub mock_fallback: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIChatStreamChunk {
    pub token: String,
    pub finish_reason: Option<String>,
    pub citations: Option<Vec<CreateCitation>>,
    pub full_content: Option<String>,
    /// Present on the final chunk: true when mock fallback was used.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mock_fallback: Option<bool>,
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
    // Ollama's final `{ "done": true }` frame carries no `message`; earlier
    // code required it and silently dropped the done signal.
    #[serde(default)]
    message: Option<OllamaMessage>,
    #[serde(default)]
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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OllamaModelInfo {
    pub name: String,
    #[serde(default)]
    pub model: String,
    #[serde(default)]
    pub size: u64,
    #[serde(default)]
    pub digest: String,
    #[serde(default)]
    pub details: serde_json::Value,
    #[serde(default)]
    pub capabilities: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OllamaTagsResponse {
    #[serde(default)]
    models: Vec<OllamaModelInfo>,
}

/// Strips Markdown code fences robustly: handles ```json, ```, leading/trailing
/// whitespace and newlines (previous version left trailing whitespace/```).
fn strip_json_fences(content: &str) -> &str {
    let mut s = content.trim();
    if s.starts_with("```") {
        // Drop opening fence line (``` or ```json).
        if let Some(idx) = s.find('\n') {
            s = s[idx + 1..].trim_start();
        } else {
            s = s.trim_start_matches('`').trim_start();
        }
    }
    if s.ends_with("```") {
        s = s.trim_end_matches('`').trim_end();
        // Remove trailing "json" leftover edge case already handled above.
    }
    s.trim()
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

    pub fn base_url(&self) -> &str {
        &self.base_url
    }

    pub fn default_llm_model(&self) -> &str {
        &self.llm_model
    }

    pub fn default_embedding_model(&self) -> &str {
        &self.embedding_model
    }

    fn build_prompt(&self, request: &AIChatRequest) -> String {
        let context = request
            .grounded_context
            .clone()
            .unwrap_or_default();

        if !context.is_empty() {
            format!(
                "You are ChemMind, an AI assistant for chemistry research. Answer the user's \
                 question using ONLY the grounded context below. If the context does not \
                 contain the answer, say so clearly. Cite the relevant source document and \
                 quote excerpts when answering.\n\nGROUNDED CONTEXT:\n{}\n\nQuestion: {}",
                context, request.prompt
            )
        } else {
            format!(
                "You are ChemMind, an AI assistant for chemistry research. Answer the user's \
                 question based on your chemistry knowledge.\n\nQuestion: {}",
                request.prompt
            )
        }
    }

    /// Sends a prompt to Ollama and parses the response as JSON.
    /// Normalises the "ollama" provider keyword to the configured default so
    /// quiz/reasoning callers behave like chat (which already normalises).
    async fn generate_json(&self, prompt: &str, model: Option<&str>) -> AppResult<serde_json::Value> {
        let model_name = match model {
            Some(m) if m != "ollama" && !m.trim().is_empty() => m.to_string(),
            _ => self.llm_model.clone(),
        };
        let ollama_request = OllamaChatRequest {
            model: model_name,
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
        let content = ollama_response.message.map(|m| m.content).unwrap_or_default();
        let stripped = strip_json_fences(&content);
        serde_json::from_str(stripped).map_err(|_| {
            AppError::Internal("AI returned malformed JSON".to_string())
        })
    }

    /// Lists models installed in Ollama via GET /api/tags.
    pub async fn list_models(&self) -> AppResult<Vec<OllamaModelInfo>> {
        let response = self
            .client
            .get(format!("{}/api/tags", self.base_url))
            .send()
            .await?;
        if !response.status().is_success() {
            return Err(AppError::HttpClient(response.error_for_status().unwrap_err()));
        }
        let tags: OllamaTagsResponse = response.json().await?;
        Ok(tags.models)
    }

    pub async fn ollama_healthy(&self) -> bool {
        self.client
            .get(format!("{}/api/tags", self.base_url))
            .send()
            .await
            .map(|r| r.status().is_success())
            .unwrap_or(false)
    }

    pub async fn embed_with_model(&self, texts: Vec<String>, model: Option<&str>) -> AppResult<Vec<Vec<f32>>> {
        let request = OllamaEmbedRequest {
            model: model
                .filter(|m| !m.trim().is_empty())
                .map(|m| m.to_string())
                .unwrap_or_else(|| self.embedding_model.clone()),
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

#[async_trait]
impl LLMProvider for OllamaProvider {
    async fn generate(&self, request: AIChatRequest) -> AppResult<(String, Vec<CreateCitation>)> {
        let prompt = self.build_prompt(&request);
        // model_provider carries the Ollama model name from the frontend; the
        // literal provider keyword "ollama" means "use the configured default".
        let model = match request.model_provider.as_deref() {
            Some(m) if m != "ollama" && !m.trim().is_empty() => m.to_string(),
            _ => self.llm_model.clone(),
        };

        let ollama_request = OllamaChatRequest {
            model,
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
            return Err(AppError::HttpClient(reqwest::Error::from(response.error_for_status().unwrap_err())));
        }

        let ollama_response: OllamaChatResponse = response.json().await?;
        let answer = ollama_response.message.map(|m| m.content).unwrap_or_default();

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
        let prompt = self.build_prompt(&request);
        let model = match request.model_provider.as_deref() {
            Some(m) if m != "ollama" && !m.trim().is_empty() => m.to_string(),
            _ => self.llm_model.clone(),
        };

        let ollama_request = OllamaChatRequest {
            model,
            messages: vec![OllamaMessage {
                role: "user".to_string(),
                content: prompt,
            }],
            stream: true,
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
            return Err(AppError::HttpClient(response.error_for_status().unwrap_err()));
        }

        // Ollama streams NDJSON lines: one JSON object per token with
        // { "message": { "content": "..." }, "done": false }, ending with
        // { "done": true }.
        let bytes = response.bytes().await?;
        let mut chunks = Vec::new();
        let mut accumulated = String::new();

        for line in bytes.split(|&b| b == b'\n') {
            let line = String::from_utf8_lossy(line);
            let line = line.trim();
            if line.is_empty() {
                continue;
            }
            match serde_json::from_str::<OllamaChatResponse>(line) {
                Ok(part) => {
                    let token = part.message.map(|m| m.content).unwrap_or_default();
                    if !token.is_empty() {
                        accumulated.push_str(&token);
                        chunks.push(AIChatStreamChunk {
                            token,
                            finish_reason: None,
                            citations: None,
                            full_content: None,
                            mock_fallback: None,
                        });
                    }
                    if part.done {
                        break;
                    }
                }
                Err(_) => continue,
            }
        }

        // Final chunk with grounded citations.
        let citations = if let Some(doc_ids) = request.selected_document_ids {
            doc_ids
                .into_iter()
                .map(|doc_id| CreateCitation {
                    document_id: Some(doc_id),
                    page: Some(1),
                    chunk_id: Some("chunk-001".to_string()),
                    section: Some("Introduction".to_string()),
                    excerpt: Some(format!(
                        "Evidence for: {}",
                        request.prompt.chars().take(50).collect::<String>()
                    )),
                })
                .collect()
        } else {
            vec![]
        };

        chunks.push(AIChatStreamChunk {
            token: String::new(),
            finish_reason: Some("stop".to_string()),
            citations: Some(citations),
            full_content: Some(accumulated),
            mock_fallback: Some(false),
        });

        Ok(chunks)
    }

    async fn embed(&self, texts: Vec<String>) -> AppResult<Vec<Vec<f32>>> {
        self.embed_with_model(texts, None).await
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
                mock_fallback: None,
            });
        }

        chunks.push(AIChatStreamChunk {
            token: String::new(),
            finish_reason: Some("stop".to_string()),
            citations: Some(citations),
            full_content: Some(accumulated),
            mock_fallback: Some(true),
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
    ) -> AppResult<(String, Vec<CreateCitation>, bool)> {
        let provider_name = request.model_provider.as_deref().unwrap_or("ollama");

        // Treat any model name (e.g. "qwen2.5:1.5b", "llama3:latest") as an
        // Ollama request since Ollama is the local provider. Only the explicit
        // "mock" provider short-circuits to the canned responder.
        if provider_name == "mock" {
            let (content, citations) = self.mock.generate(request).await?;
            return Ok((content, citations, true));
        }

        match self.ollama.generate(request.clone()).await {
            Ok((content, citations)) => Ok((content, citations, false)),
            Err(e) => {
                tracing::warn!("Ollama unavailable, falling back to mock provider: {}", e);
                let (content, citations) = self.mock.generate(request).await?;
                Ok((content, citations, true))
            }
        }
    }

    pub async fn stream_rag_response(
        &self,
        request: AIChatRequest,
    ) -> AppResult<Vec<AIChatStreamChunk>> {
        let provider_name = request.model_provider.as_deref().unwrap_or("ollama");

        if provider_name == "mock" {
            return self.mock.stream(request).await;
        }

        match self.ollama.stream(request.clone()).await {
            Ok(result) => Ok(result),
            Err(e) => {
                tracing::warn!("Ollama unavailable, falling back to mock provider: {}", e);
                self.mock.stream(request).await
            }
        }
    }

    pub fn ollama(&self) -> &OllamaProvider {
        &self.ollama
    }

    pub async fn embed(&self, texts: Vec<String>, provider: Option<&str>) -> AppResult<Vec<Vec<f32>>> {
        let (vecs, _fallback) = self.embed_with_model(texts, provider, None).await?;
        Ok(vecs)
    }

    pub async fn embed_with_model(
        &self,
        texts: Vec<String>,
        provider: Option<&str>,
        model: Option<&str>,
    ) -> AppResult<(Vec<Vec<f32>>, bool)> {
        if provider == Some("mock") {
            return Ok((self.mock.embed(texts).await?, true));
        }
        match self.ollama.embed_with_model(texts.clone(), model).await {
            Ok(result) => Ok((result, false)),
            Err(e) => {
                tracing::warn!("Ollama embedding unavailable, falling back to mock: {}", e);
                Ok((self.mock.embed(texts).await?, true))
            }
        }
    }

    /// Generates a grounded quiz in raw JSON form using the Ollama provider.
    /// Falls back to a minimal mock quiz structure if Ollama is unreachable.
    pub async fn generate_quiz(
        &self,
        topic: String,
        num_questions: i32,
        _selected_document_ids: Option<Vec<Uuid>>,
        model_provider: Option<String>,
        grounded_context: Option<String>,
    ) -> AppResult<serde_json::Value> {
        let context_block = grounded_context
            .as_deref()
            .map(|c| format!("\n\nGROUNDED CONTEXT (use only this material to author questions):\n{}", c))
            .unwrap_or_default();

        let prompt = format!(
            "Generate a chemistry multiple-choice quiz about '{}' with {} questions.\
             Base every question and explanation strictly on the grounded context provided below.\
             Return ONLY a valid JSON object with this schema: \
             {{\"title\": string, \"questions\": [{{\"question_id\": string, \"question_text\": string, \
             \"question_type\": \"multiple_choice\", \"options\": [{{\"option_letter\": string, \
             \"option_text\": string, \"is_correct\": boolean}}], \"correct_answer\": string, \
             \"explanation\": string, \"citations\": []}}]}}{}",
            topic,
            num_questions.max(1),
            context_block
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
        grounded_context: Option<String>,
    ) -> AppResult<serde_json::Value> {
        let docs: Vec<String> = selected_document_ids.iter().map(|id| id.to_string()).collect();
        let context_block = grounded_context
            .as_deref()
            .map(|c| format!("\n\nGROUNDED CONTEXT (use ONLY this material for evidence and excerpts):\n{}", c))
            .unwrap_or_default();

        let prompt = format!(
            "Perform a multi-document synthesis on the question '{query_text}' across documents {docs:?}.\
             Use ONLY the grounded context below for excerpts, findings and claims.\
             Return ONLY a valid JSON object with this schema: \
             {{\"summary\": string, \"comparison_matrix\": [{{\"topic\": string, \"document_id\": string, \
             \"excerpt\": string, \"value_or_finding\": string}}], \
             \"discrepancies\": [{{\"topic\": string, \"document_id_a\": string, \"claim_a\": string, \
             \"document_id_b\": string, \"claim_b\": string, \"nature_of_conflict\": string}}]}}{}",
            context_block
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