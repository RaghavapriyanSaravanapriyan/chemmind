-- ChemMind Document Content
-- Version: 2
-- Description: Store extracted document text so chat/quizzes/reasoning can
-- ground answers in real document excerpts (real RAG context), with citations
-- tied to the actual source document.

ALTER TABLE documents ADD COLUMN extracted_text TEXT;
CREATE INDEX idx_documents_extracted ON documents(extracted_text);