from pathlib import Path


FRONTEND_ROOT = Path(__file__).parents[1] / "frontend" / "src"
API_SOURCE = FRONTEND_ROOT / "lib" / "api.ts"
PROJECTS_SOURCE = FRONTEND_ROOT / "app" / "projects" / "page.tsx"
WORKSPACE_SOURCE = FRONTEND_ROOT / "app" / "projects" / "[id]" / "page.tsx"
VISUALISE_SOURCE = FRONTEND_ROOT / "components" / "workspace" / "VisualiseModal.tsx"


EXPECTED_API_SERVICES = (
    "fetchWorkspaces",
    "createWorkspace",
    "deleteWorkspace",
    "createConversation",
    "sendChatMessageSync",
    "fetchChemistry3D",
    "fetchChemistryProperties",
    "fetchQuiz",
    "fetchMultiDocAnalysis",
)


def test_frontend_api_exposes_all_services():
    source = API_SOURCE.read_text(encoding="utf-8")
    missing = [name for name in EXPECTED_API_SERVICES if f"export async function {name}" not in source]
    assert not missing, f"Missing frontend service exports: {missing}"


def test_project_controls_are_wired():
    source = PROJECTS_SOURCE.read_text(encoding="utf-8")
    for control in ("Create Project", "Rename", "Delete"):
        assert control in source
    assert "createWorkspace" in source
    assert "deleteWorkspace" in source


def test_workspace_controls_are_wired():
    source = WORKSPACE_SOURCE.read_text(encoding="utf-8")
    for control in ("Generate Quiz", "Multi-Doc Synthesis", "3D Visualise"):
        assert control in source
    for service in ("createConversation", "sendChatMessageSync", "fetchQuiz", "fetchMultiDocAnalysis"):
        assert service in source


def test_visualise_controls_use_chemistry_services():
    source = VISUALISE_SOURCE.read_text(encoding="utf-8")
    assert "fetchChemistry3D" in source
    assert "fetchChemistryProperties" in source
    assert "Compute 3D Structure" in source
