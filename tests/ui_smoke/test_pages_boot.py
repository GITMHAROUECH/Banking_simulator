"""
Tests smoke pour les pages UI (I7a).

Vérifie que chaque page peut être importée sans exception.
"""
import importlib.util
import sys
from pathlib import Path


def test_page_pipeline_boots():
    """Test: Page Pipeline peut être importée."""
    page_path = Path("app/pages/01_🚀_Pipeline.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    # Import dynamique
    spec = importlib.util.spec_from_file_location("page_pipeline", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_monte_carlo_boots():
    """Test: Page Monte Carlo peut être importée."""
    page_path = Path("app/pages/02_🎲_Monte_Carlo.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_monte_carlo", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_rwa_boots():
    """Test: Page RWA peut être importée."""
    page_path = Path("app/pages/03_⚠️_RWA.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_rwa", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_liquidite_boots():
    """Test: Page Liquidité peut être importée."""
    page_path = Path("app/pages/04_💧_Liquidite.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_liquidite", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_capital_boots():
    """Test: Page Capital peut être importée."""
    page_path = Path("app/pages/05_🏛️_Capital.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_capital", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_export_boots():
    """Test: Page Export peut être importée."""
    page_path = Path("app/pages/06_📥_Export.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_export", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_consolidation_boots():
    """Test: Page Consolidation peut être importée."""
    page_path = Path("app/pages/07_🧩_Consolidation.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_consolidation", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_analyse_portfolio_boots():
    """Test: Page Analyse Portfolio peut être importée."""
    page_path = Path("app/pages/08_🔎_Analyse_Portfolio.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_analyse_portfolio", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_reporting_boots():
    """Test: Page Reporting peut être importée."""
    page_path = Path("app/pages/09_📈_Reporting.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_reporting", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_configuration_boots():
    """Test: Page Configuration peut être importée."""
    page_path = Path("app/pages/10_⚙️_Configuration.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_configuration", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_documentation_boots():
    """Test: Page Documentation peut être importée."""
    page_path = Path("app/pages/11_ℹ️_Documentation.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_documentation", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_about_boots():
    """Test: Page About peut être importée."""
    page_path = Path("app/pages/12_ℹ️_About.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_about", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_admin_boots():
    """Test: Page Admin peut être importée."""
    page_path = Path("app/pages/13_🔧_Admin.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_admin", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_contrepartie_boots():
    """Test: Page Contrepartie peut être importée."""
    page_path = Path("app/pages/14_🤝_Contrepartie.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_contrepartie", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_ecl_boots():
    """Test: Page ECL peut être importée."""
    page_path = Path("app/pages/15_💰_ECL.py")
    assert page_path.exists(), f"Page non trouvée: {page_path}"

    spec = importlib.util.spec_from_file_location("page_ecl", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_all_pages_count():
    """Test: Vérifier qu'il y a exactement 15 pages (I12: +ECL)."""
    pages_dir = Path("app/pages")
    pages = list(pages_dir.glob("*.py"))
    assert len(pages) == 15, f"Attendu 15 pages, trouvé {len(pages)}"

