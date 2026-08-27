import io
import unittest
import asyncio
import pypdf
from ai.ingestion.pipeline import IngestionPipeline
from ai.ingestion.pdf_parser import PDFDocumentParser
from ai.ingestion.extractor import (
    clean_text,
    classify_block_type,
    extract_section_title,
    compute_checksum,
)
from ai.schemas.ingestion import BlockType

def create_sample_pdf_bytes() -> bytes:
    """Helper creating a 2-page sample PDF in-memory using pypdf."""
    writer = pypdf.PdfWriter()
    # Page 1
    page1 = writer.add_blank_page(width=600, height=800)
    # Page 2
    page2 = writer.add_blank_page(width=600, height=800)
    
    # Write metadata
    writer.add_metadata({
        "/Title": "Synthesis of Benzene Derivatives",
        "/Author": "Dr. Chemist",
    })
    
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()

class TestExtractorUtils(unittest.TestCase):

    def test_clean_text(self):
        raw = "   Line 1  with  spaces \x00\n\n\nLine 2   "
        cleaned = clean_text(raw)
        self.assertNotIn("\x00", cleaned)
        self.assertNotIn("\n\n\n", cleaned)
        self.assertIn("Line 1 with spaces", cleaned)

    def test_classify_block_type(self):
        self.assertEqual(classify_block_type("1. Introduction"), BlockType.HEADING)
        self.assertEqual(classify_block_type("Experimental Section"), BlockType.HEADING)
        self.assertEqual(classify_block_type("Table 1: Reaction yields"), BlockType.TABLE)
        self.assertEqual(classify_block_type("Figure 2: Molecular orbital energy levels"), BlockType.FIGURE)
        self.assertEqual(classify_block_type("Standard paragraph text."), BlockType.TEXT)

    def test_compute_checksum(self):
        checksum = compute_checksum(b"test data")
        self.assertTrue(len(checksum) == 64)  # SHA256 length

class TestPDFParserAndPipeline(unittest.TestCase):

    def test_parse_sample_pdf_bytes(self):
        async def run_test():
            pdf_bytes = create_sample_pdf_bytes()
            parser = PDFDocumentParser()
            
            doc = await parser.parse_bytes(
                file_bytes=pdf_bytes,
                filename="sample.pdf",
                workspace_id="ws_test",
                document_id="doc_test"
            )

            self.assertEqual(doc.document_id, "doc_test")
            self.assertEqual(doc.workspace_id, "ws_test")
            self.assertEqual(doc.total_pages, 2)
            self.assertEqual(doc.metadata.title, "Synthesis of Benzene Derivatives")
            self.assertEqual(doc.metadata.author, "Dr. Chemist")
            self.assertEqual(doc.metadata.mime_type, "application/pdf")
            self.assertIsNotNone(doc.metadata.checksum)

        asyncio.run(run_test())

    def test_ingestion_pipeline_routing(self):
        async def run_test():
            pipeline = IngestionPipeline()
            pdf_bytes = create_sample_pdf_bytes()

            doc = await pipeline.ingest_bytes(
                file_bytes=pdf_bytes,
                filename="test_paper.pdf",
                workspace_id="ws_101",
                document_id="doc_101",
                mime_type="application/pdf"
            )
            self.assertEqual(doc.filename, "test_paper.pdf")
            self.assertEqual(doc.total_pages, 2)

            # Test unsupported format raises error
            with self.assertRaises(ValueError):
                await pipeline.ingest_bytes(
                    file_bytes=b"dummy",
                    filename="test.unsupported",
                    workspace_id="ws_101",
                    document_id="doc_102",
                    mime_type="invalid/mime"
                )

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
