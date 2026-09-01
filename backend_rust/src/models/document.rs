use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Document {
    pub id: Uuid,
    pub workspace_id: Uuid,
    pub uploaded_by_id: Uuid,
    pub filename: String,
    pub file_size: i64,
    pub mime_type: String,
    pub storage_path: String,
    pub status: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub extracted_text: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct DocumentMetadata {
    pub id: Uuid,
    pub document_id: Uuid,
    pub page_count: Option<i32>,
    pub title: Option<String>,
    pub author: Option<String>,
    pub checksum: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentResponse {
    pub id: Uuid,
    pub workspace_id: Uuid,
    pub uploaded_by_id: Uuid,
    pub filename: String,
    pub file_size: i64,
    pub mime_type: String,
    pub storage_path: String,
    pub status: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub doc_metadata: Option<DocumentMetadataResponse>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentMetadataResponse {
    pub id: Uuid,
    pub document_id: Uuid,
    pub page_count: Option<i32>,
    pub title: Option<String>,
    pub author: Option<String>,
    pub checksum: Option<String>,
}

impl From<Document> for DocumentResponse {
    fn from(doc: Document) -> Self {
        Self {
            id: doc.id,
            workspace_id: doc.workspace_id,
            uploaded_by_id: doc.uploaded_by_id,
            filename: doc.filename,
            file_size: doc.file_size,
            mime_type: doc.mime_type,
            storage_path: doc.storage_path,
            status: doc.status,
            created_at: doc.created_at,
            updated_at: doc.updated_at,
            doc_metadata: None,
        }
    }
}

impl From<DocumentMetadata> for DocumentMetadataResponse {
    fn from(meta: DocumentMetadata) -> Self {
        Self {
            id: meta.id,
            document_id: meta.document_id,
            page_count: meta.page_count,
            title: meta.title,
            author: meta.author,
            checksum: meta.checksum,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DocumentStatusUpdate {
    pub status: String,
}