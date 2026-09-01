use axum::{
    extract::{Path, State},
    routing::post,
    Json, Router,
};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::AppResult;
use crate::middleware::AuthUser;
use crate::services::ai_gateway::AIGateway;
use crate::services::usage::UsageService;

#[derive(Deserialize)]
pub struct QuizRequest {
    pub topic: Option<String>,
    pub num_questions: Option<i32>,
    pub selected_document_ids: Option<Vec<Uuid>>,
    pub model_provider: Option<String>,
}

#[derive(Serialize)]
pub struct QuizResponse {
    pub quiz_id: Uuid,
    pub title: String,
    pub questions: Vec<QuizQuestion>,
    pub workspace_id: Uuid,
}

#[derive(Serialize)]
pub struct QuizQuestion {
    pub question_id: String,
    pub question_text: String,
    pub question_type: String,
    pub options: Vec<QuizOption>,
    pub correct_answer: String,
    pub explanation: String,
    pub citations: Vec<serde_json::Value>,
}

#[derive(Serialize)]
pub struct QuizOption {
    pub option_letter: String,
    pub option_text: String,
    pub is_correct: bool,
}

pub fn router() -> Router<crate::AppState> {
    Router::new().route(
        "/:workspace_id/quizzes",
        post(generate_quiz),
    )
}

async fn generate_quiz(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    State(ai_gateway): State<AIGateway>,
    auth_user: AuthUser,
    Path(workspace_id): Path<Uuid>,
    Json(payload): Json<QuizRequest>,
) -> AppResult<Json<QuizResponse>> {
    crate::api::v1::workspaces::get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;

    UsageService::check_quota_available(&pool, workspace_id, "ai_requests", 1, &settings).await?;
    UsageService::record_usage(&pool, workspace_id, auth_user.id(), "ai_requests", 1).await?;

    let topic = payload.topic.unwrap_or_else(|| "General Chemistry".to_string());
    let num_questions = payload.num_questions.unwrap_or(3);

    let value = ai_gateway
        .generate_quiz(topic.clone(), num_questions, payload.selected_document_ids, payload.model_provider)
        .await?;

    let questions: Vec<QuizQuestion> = value
        .get("questions")
        .and_then(|q| q.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|item| {
                    let options: Vec<QuizOption> = item
                        .get("options")
                        .and_then(|o| o.as_array())
                        .map(|arr| {
                            arr.iter()
                                .filter_map(|opt| {
                                    Some(QuizOption {
                                        option_letter: opt.get("option_letter")?.as_str()?.to_string(),
                                        option_text: opt.get("option_text")?.as_str()?.to_string(),
                                        is_correct: opt.get("is_correct").and_then(|c| c.as_bool()).unwrap_or(false),
                                    })
                                })
                                .collect()
                        })
                        .unwrap_or_default();

                    Some(QuizQuestion {
                        question_id: item.get("question_id").and_then(|s| s.as_str()).unwrap_or("q").to_string(),
                        question_text: item.get("question_text").and_then(|s| s.as_str()).unwrap_or("").to_string(),
                        question_type: item.get("question_type").and_then(|s| s.as_str()).unwrap_or("multiple_choice").to_string(),
                        options,
                        correct_answer: item.get("correct_answer").and_then(|s| s.as_str()).unwrap_or("A").to_string(),
                        explanation: item.get("explanation").and_then(|s| s.as_str()).unwrap_or("").to_string(),
                        citations: item.get("citations").and_then(|c| c.as_array()).cloned().unwrap_or_default(),
                    })
                })
                .collect()
        })
        .unwrap_or_default();

    let title = value
        .get("title")
        .and_then(|t| t.as_str())
        .unwrap_or("Generated Quiz")
        .to_string();

    Ok(Json(QuizResponse {
        quiz_id: Uuid::new_v4(),
        title,
        questions,
        workspace_id,
    }))
}
