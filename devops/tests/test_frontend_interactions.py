from pathlib import Path
import pytest

FRONTEND_SRC = Path(__file__).resolve().parents[2] / "frontend" / "src"
API_FILE = FRONTEND_SRC / "lib" / "api.ts"
PROJECTS_PAGE = FRONTEND_SRC / "app" / "projects" / "page.tsx"
WORKSPACE_PAGE = FRONTEND_SRC / "app" / "projects" / "[id]" / "page.tsx"
VISUALISE_MODAL = FRONTEND_SRC / "components" / "workspace" / "VisualiseModal.tsx"
LATEX_DOC = FRONTEND_SRC / "components" / "workspace" / "LatexDocument.tsx"


def test_frontend_api_exported_functions():
    content = API_FILE.read_text(encoding="utf-8")
    expected_functions = [
        "fetchWorkspaces",
        "createWorkspace",
        "deleteWorkspace",
        "getLocalWorkspaces",
        "saveLocalWorkspaces",
        "getLocalDocuments",
        "saveLocalDocuments",
        "getLocalMessages",
        "saveLocalMessages",
        "createConversation",
        "sendChatMessageSync",
        "fetchChemistry3D",
        "fetchChemistryProperties",
        "fetchQuiz",
        "fetchMultiDocAnalysis",
    ]
    for fn in expected_functions:
        assert f"export function {fn}" in content or f"export async function {fn}" in content, f"Missing export {fn} in api.ts"


def test_projects_page_interactive_elements_wired():
    content = PROJECTS_PAGE.read_text(encoding="utf-8")
    assert "New Project" in content
    assert "Rename Project" in content
    assert "Delete Project" in content
    assert "handleCreate" in content
    assert "handleDelete" in content
    assert "handleRenameSubmit" in content
    assert "createWorkspace" in content
    assert "deleteWorkspace" in content


def test_workspace_page_interactive_elements_wired():
    content = WORKSPACE_PAGE.read_text(encoding="utf-8")
    assert "Generate Quiz" in content
    assert "Multi-Doc Synthesis" in content
    assert "3D Visualise" in content
    assert "handleSendMessage" in content
    assert "onFileChange" in content
    assert "fetchQuiz" in content
    assert "fetchMultiDocAnalysis" in content
    assert "LatexDocument" in content
    assert "VisualiseModal" in content


def test_visualise_modal_chemistry_integration():
    content = VISUALISE_MODAL.read_text(encoding="utf-8")
    assert "fetchChemistry3D" in content
    assert "fetchChemistryProperties" in content
    assert "Compute 3D Structure" in content
    assert "RotateCcw" in content
    assert "Export Coordinates" in content


def test_latex_document_renderer_structure():
    content = LATEX_DOC.read_text(encoding="utf-8")
    assert "katex.renderToString" in content
    assert "\\section{" in content
    assert "\\subsection{" in content
    assert "$$" in content
