use sqlx::PgPool;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::models::usage::{QuotaLimits, UsageRecord, WorkspaceUsageSummary};

pub struct UsageService;

impl UsageService {
    pub async fn record_usage(
        pool: &PgPool,
        workspace_id: Uuid,
        user_id: Uuid,
        metric_type: &str,
        amount: i64,
    ) -> AppResult<UsageRecord> {
        let record = sqlx::query_as!(
            UsageRecord,
            r#"
            INSERT INTO usage_records (workspace_id, user_id, metric_type, count)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (workspace_id, metric_type) DO UPDATE SET
                count = usage_records.count + EXCLUDED.count,
                updated_at = NOW(),
                user_id = EXCLUDED.user_id
            RETURNING id, workspace_id, user_id, metric_type, count, created_at, updated_at
            "#,
            workspace_id,
            user_id,
            metric_type,
            amount
        )
        .fetch_one(pool)
        .await?;

        Ok(record)
    }

    pub async fn get_workspace_usage_summary(
        pool: &PgPool,
        workspace_id: Uuid,
        settings: &Settings,
    ) -> AppResult<WorkspaceUsageSummary> {
        let records = sqlx::query_as!(
            UsageRecord,
            r#"
            SELECT id, workspace_id, user_id, metric_type, count, created_at, updated_at
            FROM usage_records
            WHERE workspace_id = $1
            "#,
            workspace_id
        )
        .fetch_all(pool)
        .await?;

        let mut usage_map = std::collections::HashMap::new();
        for record in records {
            usage_map.insert(record.metric_type, record.count);
        }

        let docs_count = *usage_map.get("documents_uploaded").unwrap_or(&0);
        let storage_bytes = *usage_map.get("storage_bytes").unwrap_or(&0);
        let ai_requests_count = *usage_map.get("ai_requests").unwrap_or(&0);

        let storage_mb = (storage_bytes as f64) / (1024.0 * 1024.0);
        let storage_mb = (storage_mb * 100.0).round() / 100.0;

        let limits = QuotaLimits {
            max_documents: settings.default_workspace_doc_limit,
            max_storage_mb: settings.default_workspace_storage_mb,
            max_ai_requests: settings.default_workspace_ai_request_limit,
        };

        Ok(WorkspaceUsageSummary {
            workspace_id,
            documents_count: docs_count,
            storage_bytes,
            storage_mb,
            ai_requests_count,
            limits,
        })
    }

    pub async fn check_quota_available(
        pool: &PgPool,
        workspace_id: Uuid,
        metric_type: &str,
        incoming_amount: i64,
        settings: &Settings,
    ) -> AppResult<()> {
        let summary = Self::get_workspace_usage_summary(pool, workspace_id, settings).await?;

        match metric_type {
            "documents_uploaded" => {
                if summary.documents_count + incoming_amount > summary.limits.max_documents {
                    return Err(AppError::TooManyRequests(format!(
                        "Workspace document quota limit ({}) exceeded.",
                        summary.limits.max_documents
                    )));
                }
            }
            "storage_bytes" => {
                let incoming_mb = incoming_amount as f64 / (1024.0 * 1024.0);
                if summary.storage_mb + incoming_mb > summary.limits.max_storage_mb as f64 {
                    return Err(AppError::PayloadTooLarge(format!(
                        "Workspace storage quota limit ({}MB) exceeded.",
                        summary.limits.max_storage_mb
                    )));
                }
            }
            "ai_requests" => {
                if summary.ai_requests_count + incoming_amount > summary.limits.max_ai_requests {
                    return Err(AppError::TooManyRequests(format!(
                        "Workspace AI request quota limit ({}) exceeded.",
                        summary.limits.max_ai_requests
                    )));
                }
            }
            _ => {}
        }

        Ok(())
    }
}