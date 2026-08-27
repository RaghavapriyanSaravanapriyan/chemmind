import hashlib
import re
from typing import List, Tuple, Optional
from ai.schemas.ingestion import BlockType

# Common academic & chemistry paper section headings
SECTION_HEADING_PATTERNS = [
    r"^(?:\d+\.|\d+\.\d+)?\s*(?:Abstract|Introduction|Background|Methods|Experimental\s+Section|Results|Discussion|Conclusion|References|Supplementary\s+Information)\b",
    r"^(?:[I|V|X]+\.)\s+[A-Z]",  # Roman numerals like "I. INTRODUCTION"
    r"^\d+\.\s+[A-Z][a-zA-Z\s]{2,40}$",  # "1. Synthesis of Compound A"
]

EQUATION_PATTERNS = [
    r"\$\$.*?\$\$",
    r"\\\[.*?\\\]",
    r"^\s*(?:Eq\.|Equation)\s*\(?\d+\)?",
]

TABLE_PATTERNS = [
    r"^\s*(?:Table|Tab\.)\s+\d+",
]

FIGURE_PATTERNS = [
    r"^\s*(?:Figure|Fig\.)\s+\d+",
]

def compute_checksum(content: bytes) -> str:
    """Calculates SHA256 checksum of raw file bytes."""
    return hashlib.sha256(content).hexdigest()

def clean_text(text: str) -> str:
    """Cleans up raw extracted PDF text."""
    if not text:
        return ""
    # Normalize null characters
    text = text.replace("\x00", "")
    # Normalize multiple newlines/spaces
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def classify_block_type(text_line: str) -> BlockType:
    """Classifies a line/paragraph of text into a BlockType."""
    line = text_line.strip()
    if not line:
        return BlockType.TEXT

    # Check for section heading
    for pattern in SECTION_HEADING_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return BlockType.HEADING

    # Check for equation
    for pattern in EQUATION_PATTERNS:
        if re.search(pattern, line):
            return BlockType.EQUATION

    # Check for table caption/reference
    for pattern in TABLE_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return BlockType.TABLE

    # Check for figure caption
    for pattern in FIGURE_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return BlockType.FIGURE

    return BlockType.TEXT

def extract_section_title(text: str) -> Optional[str]:
    """Extracts section title if the text block represents a section heading."""
    cleaned = text.strip()
    if classify_block_type(cleaned) == BlockType.HEADING:
        # Take first line if multi-line
        first_line = cleaned.split("\n")[0].strip()
        return first_line[:100]
    return None
