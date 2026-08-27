use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Conversation {
    pub id: Uuid,
    pub workspace_id: Uuid,
    pub user_id: Uuid,
    pub title: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Message {
    pub id: Uuid,
    pub conversation_id: Uuid,
    pub sender: String,
    pub content: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Citation {
    pub id: Uuid,
    pub message_id: Uuid,
    pub document_id: Option<Uuid>,
    pub page: Option<i32>,
    pub chunk_id: Option<String>,
    pub section: Option<String>,
    pub excerpt: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateConversation {
    pub title: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateConversation {
    pub title: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateMessage {
    pub sender: String,
    pub content: String,
    pub citations: Vec<CreateCitation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateCitation {
    pub document_id: Option<Uuid>,
    pub page: Option<i32>,
    pub chunk_id: Option<String>,
    pub section: Option<String>,
    pub excerpt: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CitationResponse {
    pub id: Uuid,
    pub message_id: Uuid,
    pub document_id: Option<Uuid>,
    pub page: Option<i32>,
    pub chunk_id: Option<String>,
    pub section: Option<String>,
    pub excerpt: Option<String>,
    pub created_at: DateTime<Utc>,
}

impl From<Citation> for CitationResponse {
    fn from(citation: Citation) -> Self {
        Self {
            id: citation.id,
            message_id: citation.message_id,
            document_id: citation.document_id,
            page: citation.page,
            chunk_id: citation.chunk_id,
            section: citation.section,
            excerpt: citation.excerpt,
            created_at: citation.created_at,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageResponse {
    pub id: Uuid,
    pub conversation_id: Uuid,
    pub sender: String,
    pub content: String,
    pub created_at: DateTime<Utc>,
    pub citations: Vec<CitationResponse>,
}

impl From<Message> for MessageResponse {
    fn from(message: Message) -> Self {
        Self {
            id: message.id,
            conversation_id: message.conversation_id,
            sender: message.sender,
            content: message.content,
            created_at: message.created_at,
            citations: vec![],
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConversationResponse {
    pub id: Uuid,
    pub workspace_id: Uuid,
    pub user_id: Uuid,
    pub title: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub messages: Vec<MessageResponse>,
}

impl From<Conversation> for ConversationResponse {
    fn from(conv: Conversation) -> Self {
        Self {
            id: conv.id,
            workspace_id: conv.workspace_id,
            user_id: conv.user_id,
            title: conv.title,
            created_at: conv.created_at,
            updated_at: conv.updated_at,
            messages: vec![],
        }
    }
}