"""
Tests pour l'export pipeline (I8).
"""
import pytest

from src.services.pipeline_service import create_pipeline_export


def test_create_pipeline_export_xlsx():
    """Test: Export pipeline XLSX."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    export_bytes = create_pipeline_export(
        num_positions=100,
        seed=42,
        own_funds=own_funds,
        config=None,
        format="xlsx",
        compress=False,
        include_corep_stubs=True,
        use_cache=False,
    )

    assert isinstance(export_bytes, bytes)
    assert len(export_bytes) > 0


def test_create_pipeline_export_json():
    """Test: Export pipeline JSON."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    export_bytes = create_pipeline_export(
        num_positions=100,
        seed=42,
        own_funds=own_funds,
        config=None,
        format="json",
        compress=False,
        include_corep_stubs=True,
        use_cache=False,
    )

    assert isinstance(export_bytes, bytes)
    assert len(export_bytes) > 0


def test_create_pipeline_export_json_compressed():
    """Test: Export pipeline JSON compressé."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    export_bytes = create_pipeline_export(
        num_positions=100,
        seed=42,
        own_funds=own_funds,
        config=None,
        format="json",
        compress=True,
        include_corep_stubs=True,
        use_cache=False,
    )

    assert isinstance(export_bytes, bytes)
    assert len(export_bytes) > 0


def test_create_pipeline_export_parquet():
    """Test: Export pipeline Parquet."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    export_bytes = create_pipeline_export(
        num_positions=100,
        seed=42,
        own_funds=own_funds,
        config=None,
        format="parquet",
        compress=False,
        include_corep_stubs=False,
        use_cache=False,
    )

    assert isinstance(export_bytes, bytes)
    assert len(export_bytes) > 0


def test_create_pipeline_export_csv():
    """Test: Export pipeline CSV."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    export_bytes = create_pipeline_export(
        num_positions=100,
        seed=42,
        own_funds=own_funds,
        config=None,
        format="csv",
        compress=False,
        include_corep_stubs=False,
        use_cache=False,
    )

    assert isinstance(export_bytes, bytes)
    assert len(export_bytes) > 0


def test_create_pipeline_export_csv_compressed():
    """Test: Export pipeline CSV compressé (zip)."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    export_bytes = create_pipeline_export(
        num_positions=100,
        seed=42,
        own_funds=own_funds,
        config=None,
        format="csv",
        compress=True,
        include_corep_stubs=True,
        use_cache=False,
    )

    assert isinstance(export_bytes, bytes)
    assert len(export_bytes) > 0


def test_create_pipeline_export_invalid_params():
    """Test: Paramètres invalides."""
    own_funds = {
        "cet1": 1000.0,
        "tier1": 1200.0,
        "total": 1500.0,
        "leverage_exposure": 10000.0,
    }

    # num_positions <= 0
    with pytest.raises(ValueError, match="num_positions doit être > 0"):
        create_pipeline_export(
            num_positions=0,
            seed=42,
            own_funds=own_funds,
            config=None,
            format="xlsx",
            compress=False,
            include_corep_stubs=False,
            use_cache=False,
        )

    # seed < 0
    with pytest.raises(ValueError, match="seed doit être >= 0"):
        create_pipeline_export(
            num_positions=100,
            seed=-1,
            own_funds=own_funds,
            config=None,
            format="xlsx",
            compress=False,
            include_corep_stubs=False,
            use_cache=False,
        )

    # own_funds manquant
    with pytest.raises(ValueError, match="Clés manquantes"):
        create_pipeline_export(
            num_positions=100,
            seed=42,
            own_funds={"cet1": 1000.0},  # Clés manquantes
            config=None,
            format="xlsx",
            compress=False,
            include_corep_stubs=False,
            use_cache=False,
        )

