from typing import List
from ai.schemas.llm import ChatMessage, Role
from ai.schemas.retrieval import RetrievedChunk

CHEMISTRY_RAG_SYSTEM_PROMPT = """You are ChemMind AI, an expert AI research assistant specializing in chemistry, scientific literature analysis, and LaTeX research papers.

Guidelines for your response:
1. Answer the user's question STRICTLY using the provided RETRIEVED EVIDENCE context.
2. Every claim, chemical mechanism, or factual statement derived from the evidence MUST include inline citation markers matching the source block index (e.g. [1], [2]).
3. Preserve all LaTeX math notation (e.g. \\begin{equation}...\\end{equation}, $E = mc^2$) and chemical formulas (e.g. C6H12O6, H2SO4, THF, DCM) exactly as written.
4. Do NOT speculate or introduce external chemical reactions not supported by the retrieved context.
5. If the retrieved context does not contain enough information to answer the question, state: "I could not find sufficient evidence in the provided documents to answer this question."
"""

def build_rag_prompt(query: str, chunks: List[RetrievedChunk]) -> List[ChatMessage]:
    """
    Constructs a list of ChatMessage objects (system prompt + formatted context + user query)
    ready for LLMGateway execution.
    """
    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        sec_info = f" (Section: {chunk.section_title})" if chunk.section_title else ""
        chem_info = f" [Chemicals: {', '.join(chunk.chemical_entities)}]" if chunk.chemical_entities else ""
        
        block_text = (
            f"--- EVIDENCE BLOCK [{idx}] ---\n"
            f"Document ID: {chunk.document_id} | Page: {chunk.page_number}{sec_info}{chem_info}\n"
            f"{chunk.text}\n"
        )
        context_blocks.append(block_text)

    formatted_context = "\n".join(context_blocks) if context_blocks else "NO RETRIEVED EVIDENCE AVAILABLE."

    user_content = (
        f"RETRIEVED EVIDENCE CONTEXT:\n"
        f"{formatted_context}\n\n"
        f"USER QUESTION:\n"
        f"{query}"
    )

    return [
        ChatMessage(role=Role.SYSTEM, content=CHEMISTRY_RAG_SYSTEM_PROMPT),
        ChatMessage(role=Role.USER, content=user_content),
    ]
