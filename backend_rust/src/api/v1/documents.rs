use axum::{
    extract::{Multipart, Path, State},
    routing::{delete, get, post},
    Json, Router,
};
use sqlx::PgPool;
use uuid::Uuid;
use crate::config::Settings;
use crate::error::{AppError, AppResult};
use crate::middleware::AuthUser;
use crate::models::document::{Document, DocumentMetadata, DocumentResponse};
use crate::services::{storage::StorageService, usage::UsageService};
use tokio::io::AsyncWriteExt;

pub fn router() -> Router<crate::AppState> {
    Router::new()
        .route("/:workspace_id/documents", post(upload_document))
        .route("/:workspace_id/documents", get(list_documents))
        .route("/:workspace_id/documents/:document_id", get(get_document))
        .route("/:workspace_id/documents/:document_id", delete(delete_document))
}

async fn upload_document(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    auth_user: AuthUser,
    Path(workspace_id): Path<Uuid>,
    mut multipart: Multipart,
) -> AppResult<Json<DocumentResponse>> {
    // Verify workspace membership & permissions
    let workspace = crate::api::v1::workspaces::get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;
    if !["owner", "editor"].contains(&workspace.role.as_str()) {
        return Err(AppError::Forbidden("Only workspace owners or editors can upload documents".to_string()));
    }

    // Check quota
    UsageService::check_quota_available(&pool, workspace_id, "documents_uploaded", 1, &settings).await?;

    // Extract file from multipart
    let mut filename = String::new();
    let mut file_bytes = Vec::new();
    
    while let Some(mut field) = multipart.next_field().await? {
        if field.name() == Some("file") {
            filename = field.file_name().unwrap_or("document.pdf").to_string();
            while let Some(chunk) = field.chunk().await? {
                file_bytes.extend_from_slice(&chunk);
            }
            break;
        }
    }

    if filename.is_empty() {
        return Err(AppError::BadRequest("No file provided".to_string()));
    }

    let file_size = file_bytes.len() as u64;

    // Validate file extension
    let ext = std::path::Path::new(&filename)
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| format!(".{}", e.to_lowercase()))
        .unwrap_or_else(|| ".pdf".to_string());

    if !settings.allowed_extensions.iter().any(|allowed| *allowed == ext) {
        return Err(AppError::BadRequest(format!(
            "Unsupported file format '{}'. Allowed formats: {}",
            ext,
            settings.allowed_extensions.join(", ")
        )));
    }

    // Check file size
    let max_size = (settings.max_upload_size_mb as u64) * 1024 * 1024;
    if file_size > max_size {
        return Err(AppError::BadRequest(format!(
            "File size exceeds maximum allowed size of {}MB",
            settings.max_upload_size_mb
        )));
    }

    // Check storage quota
    UsageService::check_quota_available(&pool, workspace_id, "storage_bytes", file_size as i64, &settings).await?;

    // Save file - write to temp file first
    let storage_service = StorageService::new(&settings);
    let temp_path = std::env::temp_dir().join(format!("upload_{}", Uuid::new_v4()));
    let mut temp_file = tokio::fs::File::create(&temp_path).await?;
    temp_file.write_all(&file_bytes).await?;
    temp_file.flush().await?;
    drop(temp_file);
    
    let (storage_path, checksum, file_size_saved) = storage_service
        .save_upload_file(workspace_id, tokio::fs::File::open(&temp_path).await?, &filename)
        .await?;
    
    // Clean up temp file
    let _ = tokio::fs::remove_file(&temp_path).await;

    // Extract searchable text from the uploaded bytes. Text-based formats
    // (txt/md/csv/tex/json) are decoded directly; other formats store an empty
    // string so grounding simply has no context for them.
    let extracted_text = crate::services::document_text::extract_text(
        &filename,
        &file_bytes,
    );

    let mime_type = crate::services::document_text::mime_for(&filename);

    // Create Document record
    let document = sqlx::query_as!(
        Document,
        r#"
        INSERT INTO documents (workspace_id, uploaded_by_id, filename, file_size, mime_type, storage_path, status, extracted_text)
        VALUES ($1, $2, $3, $4, $5, $6, 'UPLOADED', $7)
        RETURNING id, workspace_id, uploaded_by_id, filename, file_size, mime_type, storage_path, status, created_at, updated_at, extracted_text
        "#,
        workspace_id,
        auth_user.id(),
        filename,
        file_size_saved as i64,
        mime_type,
        storage_path,
        extracted_text
    )
    .fetch_one(&pool)
    .await?;

    // Create DocumentMetadata record
    let doc_meta = sqlx::query_as!(
        DocumentMetadata,
        r#"
        INSERT INTO document_metadata (document_id, checksum, title)
        VALUES ($1, $2, $3)
        RETURNING id, document_id, page_count, title, author, checksum, created_at
        "#,
        document.id,
        checksum,
        filename
    )
    .fetch_one(&pool)
    .await?;

    // Record usage
    UsageService::record_usage(&pool, workspace_id, auth_user.id(), "documents_uploaded", 1).await?;
    UsageService::record_usage(&pool, workspace_id, auth_user.id(), "storage_bytes", file_size_saved as i64).await?;

    let mut response: DocumentResponse = document.into();
    response.doc_metadata = Some(doc_meta.into());
    
    Ok(Json(response))
}

async fn list_documents(
    State(pool): State<PgPool>,
    Path(workspace_id): Path<Uuid>,
    auth_user: AuthUser,
) -> AppResult<Json<Vec<DocumentResponse>>> {
    crate::api::v1::workspaces::get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;

    let documents = sqlx::query_as!(
        Document,
        r#"SELECT id, workspace_id, uploaded_by_id, filename, file_size, mime_type, storage_path, status, created_at, updated_at, extracted_text FROM documents WHERE workspace_id = $1 ORDER BY created_at DESC"#,
        workspace_id
    )
    .fetch_all(&pool)
    .await?;

    let mut responses = Vec::new();
    for doc in documents {
        let meta = sqlx::query_as!(
            DocumentMetadata,
            r#"SELECT id, document_id, page_count, title, author, checksum, created_at FROM document_metadata WHERE document_id = $1"#,
            doc.id
        )
        .fetch_optional(&pool)
        .await?;

        let mut resp: DocumentResponse = doc.into();
        resp.doc_metadata = meta.map(Into::into);
        responses.push(resp);
    }

    Ok(Json(responses))
}

async fn get_document(
    State(pool): State<PgPool>,
    Path((workspace_id, document_id)): Path<(Uuid, Uuid)>,
    auth_user: AuthUser,
) -> AppResult<Json<DocumentResponse>> {
    crate::api::v1::workspaces::get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;

    let document = sqlx::query_as!(
        Document,
        r#"SELECT id, workspace_id, uploaded_by_id, filename, file_size, mime_type, storage_path, status, created_at, updated_at, extracted_text FROM documents WHERE id = $1 AND workspace_id = $2"#,
        document_id,
        workspace_id
    )
    .fetch_optional(&pool)
    .await?
    .ok_or_else(|| AppError::NotFound("Document not found".to_string()))?;

    let meta = sqlx::query_as!(
        DocumentMetadata,
        r#"SELECT id, document_id, page_count, title, author, checksum, created_at FROM document_metadata WHERE document_id = $1"#,
        document_id
    )
    .fetch_optional(&pool)
    .await?;

    let mut response: DocumentResponse = document.into();
    response.doc_metadata = meta.map(Into::into);
    
    Ok(Json(response))
}

async fn delete_document(
    State(pool): State<PgPool>,
    State(settings): State<Settings>,
    Path((workspace_id, document_id)): Path<(Uuid, Uuid)>,
    auth_user: AuthUser,
) -> AppResult<()> {
    let workspace = crate::api::v1::workspaces::get_workspace_with_role(&pool, workspace_id, auth_user.id()).await?;
    if !["owner", "editor"].contains(&workspace.role.as_str()) {
        return Err(AppError::Forbidden("Only workspace owners or editors can delete documents".to_string()));
    }

    let document = sqlx::query_as!(
        Document,
        r#"SELECT id, workspace_id, uploaded_by_id, filename, file_size, mime_type, storage_path, status, created_at, updated_at, extracted_text FROM documents WHERE id = $1 AND workspace_id = $2"#,
        document_id,
        workspace_id
    )
    .fetch_optional(&pool)
    .await?
    .ok_or_else(|| AppError::NotFound("Document not found".to_string()))?;

    // Delete storage file
    let storage_service = StorageService::new(&settings);
    storage_service.delete_file(&document.storage_path);

    // Delete DB record (cascades to metadata)
    sqlx::query!("DELETE FROM documents WHERE id = $1", document_id)
        .execute(&pool)
        .await?;

    Ok(())
}