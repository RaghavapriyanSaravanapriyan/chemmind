/// Lightweight document text extraction for RAG grounding.
///
/// Text-based formats are decoded directly from bytes so chat, quizzes and
/// multi-doc reasoning can reference real document content. Binary formats
/// (PDF, DOCX) are left empty — the client keeps its own rendered preview,
/// and grounding simply has no text context for those documents.
pub fn extract_text(filename: &str, bytes: &[u8]) -> Option<String> {
    let ext = std::path::Path::new(filename)
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| e.to_lowercase())
        .unwrap_or_default();

    match ext.as_str() {
        "txt" | "md" | "csv" | "tex" | "json" | "tsv" | "log" | "rst" | "org" => {
            let text = String::from_utf8_lossy(bytes).into_owned();
            let trimmed = text.trim();
            if trimmed.is_empty() {
                None
            } else {
                Some(trimmed.to_string())
            }
        }
        _ => None,
    }
}

/// Loads extracted text for the given document IDs and builds a grounded
/// context block with real excerpts, so answers, quizzes and reasoning
/// reference actual sources rather than fabricated ones.
pub async fn build_grounded_context(
    pool: &sqlx::PgPool,
    doc_ids: &[uuid::Uuid],
) -> Option<String> {
    if doc_ids.is_empty() {
        return None;
    }

    let mut blocks = Vec::new();
    for doc_id in doc_ids {
        let doc = sqlx::query_as!(
            crate::models::document::Document,
            r#"SELECT id, workspace_id, uploaded_by_id, filename, file_size, mime_type, storage_path, status, created_at, updated_at, extracted_text FROM documents WHERE id = $1"#,
            doc_id
        )
        .fetch_optional(pool)
        .await
        .ok()
        .flatten();

        if let Some(doc) = doc {
            if let Some(text) = doc.extracted_text.as_ref() {
                let text = text.trim();
                if !text.is_empty() {
                    let excerpt: String = text.chars().take(4000).collect();
                    blocks.push(format!("[Document: {}]\n{}", doc.filename, excerpt));
                }
            }
        }
    }

    if blocks.is_empty() {
        None
    } else {
        Some(blocks.join("\n\n---\n\n"))
    }
}

/// Returns a best-effort MIME type for a filename based on its extension.
pub fn mime_for(filename: &str) -> String {
    let ext = std::path::Path::new(filename)
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| e.to_lowercase())
        .unwrap_or_default();

    match ext.as_str() {
        "pdf" => "application/pdf".to_string(),
        "txt" | "md" | "rst" | "org" | "log" => "text/plain".to_string(),
        "csv" | "tsv" => "text/csv".to_string(),
        "tex" => "application/x-tex".to_string(),
        "json" => "application/json".to_string(),
        _ => "application/octet-stream".to_string(),
    }
}

/// Splits extracted document text into reasonably-sized overlapping chunks so
/// it fits inside a prompt context window without truncating evidence.
pub fn chunk_text(text: &str, max_chars: usize, overlap: usize) -> Vec<String> {
    let text = text.trim();
    if text.is_empty() {
        return vec![];
    }

    let mut chunks = Vec::new();
    let mut start = 0usize;
    let chars: Vec<char> = text.chars().collect();

    while start < chars.len() {
        let end = (start + max_chars).min(chars.len());
        let chunk: String = chars[start..end].iter().collect();
        chunks.push(chunk);

        if end >= chars.len() {
            break;
        }
        start = end.saturating_sub(overlap);
    }

    chunks
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn extracts_text_from_plain_files() {
        assert_eq!(extract_text("notes.txt", b"hello world").as_deref(), Some("hello world"));
        assert_eq!(extract_text("paper.md", b"# Title\nBody").as_deref(), Some("# Title\nBody"));
        assert_eq!(extract_text("data.csv", b"a,b,c").as_deref(), Some("a,b,c"));
    }

    #[test]
    fn returns_none_for_binary_or_unknown_formats() {
        assert_eq!(extract_text("paper.pdf", b"%PDF-1.4"), None);
        assert_eq!(extract_text("molecule.png", b"\x89PNG"), None);
        assert_eq!(extract_text("notes", b"no extension"), None);
    }

    #[test]
    fn chunks_with_overlap() {
        let text = "abcdefghij".repeat(10);
        let chunks = chunk_text(&text, 20, 5);
        assert!(chunks.len() > 1);
        assert!(chunks.iter().all(|c| c.chars().count() <= 20));
        // Overlap means the end of one chunk appears in the next.
        assert!(chunks[1].contains(&chunks[0].chars().last().unwrap().to_string()));
    }
}