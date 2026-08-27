use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct UsageRecord {
    pub id: Uuid,
    pub workspace_id: Uuid,
    pub user_id: Uuid,
    pub metric_type: String,
    pub count: i64,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuotaLimits {
    pub max_documents: i64,
    pub max_storage_mb: i64,
    pub max_ai_requests: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceUsageSummary {
    pub workspace_id: Uuid,
    pub documents_count: i64,
    pub storage_bytes: i64,
    pub storage_mb: f64,
    pub ai_requests_count: i64,
    pub limits: QuotaLimits,
}