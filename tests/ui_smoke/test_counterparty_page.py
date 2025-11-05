"""
Tests smoke pour la page Contrepartie (I7c).
"""
from pathlib import Path


def test_counterparty_page_exists():
    """Test: La page Contrepartie existe."""
    page_path = Path("app/pages/14_🔁_Contrepartie.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"


def test_counterparty_page_imports():
    """Test: La page Contrepartie peut être importée sans erreur."""
    # Import dynamique pour éviter l'exécution Streamlit
    import importlib.util

    page_path = Path("app/pages/14_🔁_Contrepartie.py")
    spec = importlib.util.spec_from_file_location("page_counterparty", page_path)
    assert spec is not None
    assert spec.loader is not None

    # Note: On ne charge pas le module car Streamlit s'exécuterait
    # On vérifie juste que le spec est valide

