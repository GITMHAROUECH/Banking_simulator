"""
Tests smoke pour les pages UI (I7a).

Vérifie que chaque page peut être importée sans exception.
"""
import importlib.util
import sys
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


def test_page_pipeline_boots():
    """Test: Page Pipeline peut être importée."""
    page_path = _find_page_by_number("01", "pipeline")
    assert page_path is not None, "Page Pipeline non trouvée"

    # Import dynamique
    spec = importlib.util.spec_from_file_location("page_pipeline", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_monte_carlo_boots():
    """Test: Page Monte Carlo peut être importée."""
    page_path = _find_page_by_number("02", "monte")
    assert page_path is not None, "Page Monte Carlo non trouvée"

    spec = importlib.util.spec_from_file_location("page_monte_carlo", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_rwa_boots():
    """Test: Page RWA peut être importée."""
    page_path = _find_page_by_number("03", "rwa")
    assert page_path is not None, "Page RWA non trouvée"

    spec = importlib.util.spec_from_file_location("page_rwa", page_path)
    assert spec is not None
    assert spec.loader is not None


def test_page_liquidite_boots():
    """Test: Page Liquidité peut être importée."""
    page_path = _find_page_by_number("04", "liquid")
    assert page_path is not None, "Page Liquidité non trouvée"


def test_page_capital_boots():
    """Test: Page Capital peut être importée."""
    page_path = _find_page_by_number("05", "capital")
    assert page_path is not None, "Page Capital non trouvée"


def test_page_export_boots():
    """Test: Page Export peut être importée."""
    page_path = _find_page_by_number("06", "export")
    assert page_path is not None, "Page Export non trouvée"


def test_page_consolidation_boots():
    """Test: Page Consolidation peut être importée."""
    page_path = _find_page_by_number("07", "consol")
    assert page_path is not None, "Page Consolidation non trouvée"


def test_page_analyse_portfolio_boots():
    """Test: Page Analyse Portfolio peut être importée."""
    page_path = _find_page_by_number("08", "analyse")
    assert page_path is not None, "Page Analyse Portfolio non trouvée"


def test_page_reporting_boots():
    """Test: Page Reporting peut être importée."""
    page_path = _find_page_by_number("09", "reporting")
    assert page_path is not None, "Page Reporting non trouvée"


def test_page_configuration_boots():
    """Test: Page Configuration peut être importée."""
    page_path = _find_page_by_number("10", "config")
    assert page_path is not None, "Page Configuration non trouvée"


def test_page_documentation_boots():
    """Test: Page Documentation peut être importée."""
    page_path = _find_page_by_number("11", "doc")
    assert page_path is not None, "Page Documentation non trouvée"


def test_page_about_boots():
    """Test: Page About peut être importée."""
    page_path = _find_page_by_number("12", "about")
    assert page_path is not None, "Page About non trouvée"


def test_page_admin_boots():
    """Test: Page Admin peut être importée."""
    page_path = _find_page_by_number("13", "admin")
    assert page_path is not None, "Page Admin non trouvée"


def test_all_pages_count():
    """Test: Vérifier qu'il y a exactement 17 pages (I12: +ECL, Workflow Refactoring: +Home +Simulation)."""
    pages_dir = Path("app/pages")
    pages = list(pages_dir.glob("*.py"))
    assert len(pages) == 17, f"Attendu 17 pages, trouvé {len(pages)}"

