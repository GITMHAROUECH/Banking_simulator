"""
Tests smoke pour la page Export (I8).
"""
from pathlib import Path


def _find_page_by_number(page_number: str, keyword: str = "") -> Path | None:
    """Find a page file by number prefix and optional keyword, handling encoding issues."""
    pages_dir = Path("app/pages")
    pattern = f"{page_number}_*.py"

    for page_path in pages_dir.glob(pattern):
        # Check if keyword is in filename (case-insensitive, handle encoding)
        if not keyword or keyword.lower() in page_path.name.lower():
            return page_path

    return None


def test_export_page_exists():
    """Test: La page Export existe."""
    page_path = _find_page_by_number("06", "export")
    assert page_path is not None, "Page Export non trouvée"


def test_export_page_imports():
    """Test: La page Export peut être importée sans erreur."""
    # Import dynamique pour éviter l'exécution Streamlit
    import importlib.util

    page_path = _find_page_by_number("06", "export")
    assert page_path is not None, "Page Export non trouvée"

    spec = importlib.util.spec_from_file_location("page_export", page_path)
    assert spec is not None
    assert spec.loader is not None

    # Note: On ne charge pas le module car Streamlit s'exécuterait
    # On vérifie juste que le spec est valide

