use crate::error::{AppError, AppResult};
use crate::models::quiz::{QuizGenerationRequestInternal, QuizQuestion, QuizOption, QuizResponse};
use crate::models::conversation::CitationResponse;
use crate::services::ai_gateway::{AIGateway, AIChatRequest};
use uuid::Uuid;

pub struct QuizGenerator;

impl QuizGenerator {
    pub fn new() -> Self {
        Self
    }

    pub async fn generate_quiz(
        &self,
        ai_gateway: &AIGateway,
        request: QuizGenerationRequestInternal,
    ) -> AppResult<QuizResponse> {
        let topic = request.topic;
        let num_questions = request.num_questions.clamp(1, 10);
        
        let doc_context = if let Some(doc_ids) = &request.document_ids {
            format!("\n\nContext documents: {}", 
                doc_ids.iter().map(|id| id.to_string()).collect::<Vec<_>>().join(", "))
        } else {
            String::new()
        };

        let prompt = format!(
            r#"You are ChemMind, an AI assistant for chemistry research. Generate a multiple-choice quiz about "{topic}" with {num_questions} questions.{doc_context}

Return ONLY a valid JSON object matching this exact schema:
{{
  "title": "Quiz Title",
  "questions": [
    {{
      "question_id": "q1",
      "question_text": "Question text here",
      "question_type": "multiple_choice",
      "options": [
        {{"option_letter": "A", "option_text": "Option A text", "is_correct": true}},
        {{"option_letter": "B", "option_text": "Option B text", "is_correct": false}},
        {{"option_letter": "C", "option_text": "Option C text", "is_correct": false}},
        {{"option_letter": "D", "option_text": "Option D text", "is_correct": false}}
      ],
      "correct_answer": "A",
      "explanation": "Explanation for the correct answer",
      "citations": []
    }}
  ]
}}

Ensure exactly one option has is_correct: true per question. Use letters A-D for options."#,
            topic = topic,
            num_questions = num_questions,
            doc_context = doc_context
        );

        let ai_request = AIChatRequest {
            prompt,
            selected_document_ids: request.document_ids,
            model_provider: Some("ollama".to_string()),
        };

        let (response_text, _) = ai_gateway.generate_rag_response(ai_request).await?;
        
        let quiz_data: serde_json::Value = serde_json::from_str(&response_text)
            .map_err(|e| AppError::Internal(format!("Failed to parse quiz JSON: {}", e)))?;

        let title = quiz_data["title"].as_str()
            .unwrap_or("Generated Chemistry Quiz")
            .to_string();

        let mut questions = Vec::new();
        if let Some(qs) = quiz_data["questions"].as_array() {
            for (i, q) in qs.iter().enumerate() {
                let question_id = q["question_id"].as_str()
                    .unwrap_or(&format!("q{}", i + 1))
                    .to_string();

                let question_text = q["question_text"].as_str()
                    .unwrap_or("Question text not available")
                    .to_string();

                let mut options = Vec::new();
                let mut correct_answer = "A".to_string();
                if let Some(opts) = q["options"].as_array() {
                    for opt in opts {
                        let letter = opt["option_letter"].as_str().unwrap_or("A").to_string();
                        let text = opt["option_text"].as_str().unwrap_or("").to_string();
                        let is_correct = opt["is_correct"].as_bool().unwrap_or(false);
                        if is_correct {
                            correct_answer = letter.clone();
                        }
                        options.push(QuizOption {
                            option_letter: letter,
                            option_text: text,
                            is_correct,
                        });
                    }
                }

                let explanation = q["explanation"].as_str()
                    .unwrap_or("No explanation provided")
                    .to_string();

                questions.push(QuizQuestion {
                    question_id,
                    question_text,
                    question_type: "multiple_choice".to_string(),
                    options,
                    correct_answer,
                    explanation,
                    citations: vec![],
                });
            }
        }

        Ok(QuizResponse {
            quiz_id: format!("quiz-{}", Uuid::new_v4()),
            title,
            questions,
            workspace_id: request.workspace_id,
        })
    }
}