import io
import uuid
from datetime import datetime, timezone
from typing import List, Optional
import pypdf
from ai.ingestion.base import BaseDocumentParser
from ai.ingestion.extractor import (
    clean_text,
    classify_block_type,
    extract_section_title,
    compute_checksum,
)
from ai.schemas.document import DocumentMetadata
from ai.schemas.ingestion import (
    BlockType,
    ExtractedBlock,
    ParsedPage,
    IngestedDocument,
)
from ai.utils.logger import logger

class PDFDocumentParser(BaseDocumentParser):
    """Concrete Document Parser for PDF files using pypdf."""

    @property
    def supported_mime_types(self) -> List[str]:
        return ["application/pdf"]

    async def parse_file(
        self,
        file_path: str,
        workspace_id: str,
        document_id: str
    ) -> IngestedDocument:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        filename = file_path.split("/")[-1]
        return await self.parse_bytes(file_bytes, filename, workspace_id, document_id)

    async def parse_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        workspace_id: str,
        document_id: str
    ) -> IngestedDocument:
        logger.info(f"Parsing PDF document ID '{document_id}', filename '{filename}', bytes: {len(file_bytes)}")
        checksum = compute_checksum(file_bytes)
        
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        except Exception as exc:
            logger.error(f"Failed to read PDF bytes for document {document_id}: {exc}")
            raise ValueError(f"Invalid or corrupted PDF file: {exc}") from exc

        pdf_meta = reader.metadata or {}
        title = pdf_meta.title or filename
        author = pdf_meta.author
        
        doc_metadata = DocumentMetadata(
            title=title,
            author=author,
            created_at=datetime.now(timezone.utc),
            mime_type="application/pdf",
            file_size_bytes=len(file_bytes),
            total_pages=len(reader.pages),
            checksum=checksum,
        )

        parsed_pages: List[ParsedPage] = []
        total_blocks_count = 0
        current_section: Optional[str] = None

        for page_idx, page in enumerate(reader.pages):
            page_number = page_idx + 1  # 1-indexed page number
            raw_page_text = page.extract_text() or ""
            cleaned_page_text = clean_text(raw_page_text)

            # Segment page text into paragraphs/blocks
            paragraphs = [p.strip() for p in cleaned_page_text.split("\n\n") if p.strip()]
            page_blocks: List[ExtractedBlock] = []

            img_count = len(getattr(page, "images", []))
            table_count = 0

            for para in paragraphs:
                b_type = classify_block_type(para)
                
                if b_type == BlockType.HEADING:
                    new_sec = extract_section_title(para)
                    if new_sec:
                        current_section = new_sec

                if b_type == BlockType.TABLE:
                    table_count += 1

                block_id = f"{document_id}_p{page_number}_b{len(page_blocks) + 1}"
                
                block = ExtractedBlock(
                    block_id=block_id,
                    page_number=page_number,
                    block_type=b_type,
                    text=para,
                    section_title=current_section,
                )
                page_blocks.append(block)
                total_blocks_count += 1

            parsed_page = ParsedPage(
                page_number=page_number,
                text=cleaned_page_text,
                blocks=page_blocks,
                image_count=img_count,
                table_count=table_count,
            )
            parsed_pages.append(parsed_page)

        logger.info(
            f"Successfully parsed PDF '{filename}' ({len(parsed_pages)} pages, {total_blocks_count} total blocks)"
        )

        return IngestedDocument(
            document_id=document_id,
            workspace_id=workspace_id,
            filename=filename,
            metadata=doc_metadata,
            pages=parsed_pages,
            total_pages=len(parsed_pages),
            total_blocks=total_blocks_count,
        )
