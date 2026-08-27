use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::models::conversation::CitationResponse;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuizOption {
    pub option_letter: String,
    pub option_text: String,
    pub is_correct: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuizQuestion {
    pub question_id: String,
    pub question_text: String,
    pub question_type: String,
    pub options: Vec<QuizOption>,
    pub correct_answer: String,
    pub explanation: String,
    pub citations: Vec<CitationResponse>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuizRequestSchema {
    pub topic: Option<String>,
    pub num_questions: Option<i32>,
    pub document_ids: Option<Vec<Uuid>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuizResponse {
    pub quiz_id: String,
    pub title: String,
    pub questions: Vec<QuizQuestion>,
    pub workspace_id: Uuid,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuizGenerationRequestInternal {
    pub workspace_id: Uuid,
    pub topic: String,
    pub num_questions: i32,
    pub document_ids: Option<Vec<Uuid>>,
}