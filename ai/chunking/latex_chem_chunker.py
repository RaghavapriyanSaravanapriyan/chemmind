import re
from typing import List, Optional
from ai.chunking.base import BaseChunker
from ai.chunking.chem_entity_extractor import extract_chemical_entities
from ai.schemas.document import DocumentChunk
from ai.schemas.ingestion import IngestedDocument, BlockType, ExtractedBlock
from ai.utils.logger import logger

# Regex to detect LaTeX math environment start/end
LATEX_MATH_ENV_START = re.compile(r"\\begin\{(?:equation|align|eqnarray|gather|multline)\*?\}|\$\$|\\\[")
LATEX_MATH_ENV_END = re.compile(r"\\end\{(?:equation|align|eqnarray|gather|multline)\*?\}|\$\$|\\\]")

class LaTeXChemistryChunker(BaseChunker):
    """
    Structure- & Chemistry-Aware Semantic Chunker for LaTeX Research Papers.
    
    Guarantees:
    1. LaTeX equations/math environments are NEVER split across chunks.
    2. Chemical entities (formulas, solvents, SMILES, IUPAC names) are automatically tagged.
    3. 1-indexed page boundaries and section titles are strictly preserved.
    """

    def __init__(
        self,
        target_chunk_size: int = 800,
        chunk_overlap: int = 150,
        min_chunk_size: int = 100
    ):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def _is_equation_block(self, text: str) -> bool:
        if not text:
            return False
        if LATEX_MATH_ENV_START.search(text) or LATEX_MATH_ENV_END.search(text):
            return True
        if text.strip().startswith("$$") or text.strip().startswith("\\["):
            return True
        return False

    def chunk_document(self, doc: IngestedDocument) -> List[DocumentChunk]:
        logger.info(
            f"Chunking document '{doc.filename}' (ID: {doc.document_id}) with target size {self.target_chunk_size} chars"
        )
        
        chunks: List[DocumentChunk] = []
        current_text_accumulator: List[str] = []
        current_char_count = 0
        
        current_section: Optional[str] = None
        parent_section: Optional[str] = None
        current_page_start: Optional[int] = None
        current_page_end: Optional[int] = None

        def flush_chunk(force_type: Optional[str] = None):
            nonlocal current_text_accumulator, current_char_count, current_page_start, current_page_end
            
            if not current_text_accumulator:
                return

            full_text = "\n\n".join(current_text_accumulator).strip()
            if not full_text:
                current_text_accumulator = []
                current_char_count = 0
                return

            chunk_id = f"{doc.document_id}_chunk_{len(chunks) + 1}"
            chem_entities = extract_chemical_entities(full_text)
            
            # Determine chunk type
            c_type = force_type
            if not c_type:
                if self._is_equation_block(full_text):
                    c_type = "equation"
                elif full_text.startswith("Table "):
                    c_type = "table_caption"
                elif full_text.startswith("Figure ") or full_text.startswith("Fig. "):
                    c_type = "figure_caption"
                else:
                    c_type = "text"

            p_start = current_page_start or 1
            p_end = current_page_end or p_start

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=doc.document_id,
                workspace_id=doc.workspace_id,
                text=full_text,
                page_number=p_start,
                page_start=p_start,
                page_end=p_end,
                section_title=current_section,
                parent_section=parent_section,
                chunk_type=c_type,
                chemical_entities=chem_entities,
                token_count_estimate=max(1, len(full_text) // 4),
            )
            chunks.append(chunk)

            # Handle overlap: keep last part of text for next chunk if soft-flushed
            if self.chunk_overlap > 0 and len(full_text) > self.chunk_overlap and not force_type:
                overlap_text = full_text[-self.chunk_overlap:]
                current_text_accumulator = [overlap_text]
                current_char_count = len(overlap_text)
            else:
                current_text_accumulator = []
                current_char_count = 0

            current_page_start = None
            current_page_end = None

        for page in doc.pages:
            page_num = page.page_number
            
            for block in page.blocks:
                block_text = block.text.strip()
                if not block_text:
                    continue

                if not current_page_start:
                    current_page_start = page_num
                current_page_end = page_num

                # Update section tracking if heading
                if block.block_type == BlockType.HEADING:
                    if current_section and current_section != block.section_title:
                        parent_section = current_section
                    if block.section_title:
                        current_section = block.section_title
                    
                    # Flush current chunk before new section header if it has content
                    if current_char_count >= self.min_chunk_size:
                        flush_chunk()

                # Check if block is an isolated equation block (must NOT be split)
                if block.block_type == BlockType.EQUATION or self._is_equation_block(block_text):
                    # Flush any accumulated text first so the equation stands as its own atomic block (or chunk)
                    if current_char_count > 0:
                        flush_chunk()
                    
                    current_text_accumulator.append(block_text)
                    current_char_count = len(block_text)
                    flush_chunk(force_type="equation")
                    continue

                # Normal text paragraph processing
                current_text_accumulator.append(block_text)
                current_char_count += len(block_text)

                # Check if target chunk size reached
                if current_char_count >= self.target_chunk_size:
                    flush_chunk()

        # Flush any remaining text at the end of the document
        if current_text_accumulator:
            flush_chunk()

        logger.info(f"Generated {len(chunks)} DocumentChunks for '{doc.filename}'")
        return chunks
