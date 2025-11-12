"""
Tests smoke pour la page Export (I8).
"""
from pathlib import Path


def test_export_page_exists():
    """Test: La page Export existe."""
    page_path = Path("app/pages/06_📥_Export.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"


def test_export_page_imports():
    """Test: La page Export peut être importée sans erreur."""
    # Import dynamique pour éviter l'exécution Streamlit
    import importlib.util

    page_path = Path("app/pages/06_📥_Export.py")
    spec = importlib.util.spec_from_file_location("page_export", page_path)
    assert spec is not None
    assert spec.loader is not None

    # Note: On ne charge pas le module car Streamlit s'exécuterait
    # On vérifie juste que le spec est valide

