from typing import List, Optional
from pydantic import BaseModel, Field
from ai.schemas.citation import Citation

class MultiDocAnalysisRequest(BaseModel):
    document_ids: List[str] = Field(..., min_items=1, description="List of target document IDs to cross-examine")
    query_text: str = Field(..., description="Synthesis or comparative question text")
    workspace_id: str = Field(..., description="Target workspace ID")
    collection_name: str = Field(default="chem_papers", description="Vector store collection name")
    top_k_per_doc: int = Field(default=3, ge=1, le=20, description="Max candidate chunks retrieved per document")

class ComparisonMatrixItem(BaseModel):
    topic: str = Field(..., description="Aspect or reaction parameter compared (e.g. Yield, Catalyst, Temperature)")
    document_id: str = Field(..., description="Document ID")
    excerpt: str = Field(..., description="Direct quote excerpt from source chunk")
    value_or_finding: str = Field(..., description="Extracted numerical or qualitative finding")

class DiscrepancyItem(BaseModel):
    topic: str = Field(..., description="Topic of discrepancy or contradiction")
    document_id_a: str = Field(..., description="First document ID")
    claim_a: str = Field(..., description="Claim or reported value in document A")
    document_id_b: str = Field(..., description="Second document ID")
    claim_b: str = Field(..., description="Claim or reported value in document B")
    nature_of_conflict: str = Field(..., description="Scientific analysis of why claims differ")

class MultiDocAnalysisResponse(BaseModel):
    summary: str = Field(..., description="Cross-document synthesis summary text")
    comparison_matrix: List[ComparisonMatrixItem] = Field(default_factory=list, description="Structured comparative matrix across documents")
    discrepancies: List[DiscrepancyItem] = Field(default_factory=list, description="Identified discrepancies or contradictions between documents")
    citations: List[Citation] = Field(default_factory=list, description="Structured source citations across all documents")
    workspace_id: str = Field(..., description="Workspace ID")
