"""
Tests pour les exports multi-formats (I8).
"""
import gzip
import json
from io import BytesIO
from zipfile import ZipFile

import pandas as pd
import pytest

from src.services.reporting_service import create_export


@pytest.fixture
def sample_outputs():
    """Fixture: Outputs d'exemple pour les tests."""
    positions_df = pd.DataFrame(
        {
            "position_id": ["P001", "P002", "P003"],
            "exposure_class": ["Corporate", "Retail", "Sovereign"],
            "exposure": [1000000, 500000, 750000],
        }
    )

    rwa_df = pd.DataFrame(
        {
            "position_id": ["P001", "P002", "P003"],
            "exposure_class": ["Corporate", "Retail", "Sovereign"],
            "rwa": [800000, 375000, 0],
        }
    )

    lcr_df = pd.DataFrame(
        {
            "category": ["HQLA Level 1", "HQLA Level 2A", "Net Outflows"],
            "amount": [1000000, 500000, 800000],
        }
    )

    nsfr_df = pd.DataFrame(
        {
            "category": ["ASF", "RSF"],
            "amount": [1500000, 1200000],
        }
    )

    ratios = {
        "cet1_ratio": 0.15,
        "tier1_ratio": 0.17,
        "total_capital_ratio": 0.20,
        "leverage_ratio": 0.05,
    }

    return {
        "positions": positions_df,
        "rwa": rwa_df,
        "liquidity": {"lcr": lcr_df, "nsfr": nsfr_df},
        "ratios": ratios,
        "metadata": {"version": "0.8.0", "test": True},
    }


def test_create_export_xlsx(sample_outputs):
    """Test: Export XLSX multi-onglets."""
    excel_bytes = create_export(
        sample_outputs, format="xlsx", compress=False, include_corep_stubs=False
    )

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0

    # Vérifier que c'est un fichier Excel valide
    excel_file = pd.ExcelFile(BytesIO(excel_bytes))
    sheet_names = excel_file.sheet_names

    # Vérifier la présence des onglets attendus
    assert "Positions" in sheet_names
    assert "RWA" in sheet_names
    assert "LCR" in sheet_names
    assert "NSFR" in sheet_names
    assert "Ratios Capital" in sheet_names
    assert "Meta" in sheet_names


def test_create_export_xlsx_with_corep_stubs(sample_outputs):
    """Test: Export XLSX avec stubs COREP."""
    excel_bytes = create_export(
        sample_outputs, format="xlsx", compress=False, include_corep_stubs=True
    )

    excel_file = pd.ExcelFile(BytesIO(excel_bytes))
    sheet_names = excel_file.sheet_names

    # Vérifier la présence des stubs COREP
    assert "COREP C07" in sheet_names
    assert "COREP C08" in sheet_names
    assert "Leverage" in sheet_names
    assert "LCR" in sheet_names


def test_create_export_parquet(sample_outputs):
    """Test: Export Parquet."""
    parquet_bytes = create_export(
        sample_outputs, format="parquet", compress=False, include_corep_stubs=False
    )

    assert isinstance(parquet_bytes, bytes)
    assert len(parquet_bytes) > 0

    # Vérifier que c'est un fichier Parquet valide
    df = pd.read_parquet(BytesIO(parquet_bytes))
    assert not df.empty
    assert "position_id" in df.columns


def test_create_export_parquet_compressed(sample_outputs):
    """Test: Export Parquet compressé (gzip)."""
    parquet_bytes = create_export(
        sample_outputs, format="parquet", compress=True, include_corep_stubs=False
    )

    assert isinstance(parquet_bytes, bytes)
    assert len(parquet_bytes) > 0

    # Vérifier que c'est un fichier Parquet valide
    df = pd.read_parquet(BytesIO(parquet_bytes))
    assert not df.empty


def test_create_export_csv(sample_outputs):
    """Test: Export CSV simple."""
    csv_bytes = create_export(
        sample_outputs, format="csv", compress=False, include_corep_stubs=False
    )

    assert isinstance(csv_bytes, bytes)
    assert len(csv_bytes) > 0

    # Vérifier que c'est un CSV valide
    csv_str = csv_bytes.decode("utf-8")
    assert "position_id" in csv_str
    assert "P001" in csv_str


def test_create_export_csv_compressed(sample_outputs):
    """Test: Export CSV compressé (zip multi-fichiers)."""
    csv_bytes = create_export(
        sample_outputs, format="csv", compress=True, include_corep_stubs=True
    )

    assert isinstance(csv_bytes, bytes)
    assert len(csv_bytes) > 0

    # Vérifier que c'est un ZIP valide
    with ZipFile(BytesIO(csv_bytes), "r") as zipf:
        filenames = zipf.namelist()

        # Vérifier la présence des fichiers attendus
        assert "positions.csv" in filenames
        assert "rwa.csv" in filenames
        assert "lcr.csv" in filenames
        assert "nsfr.csv" in filenames
        assert "ratios.csv" in filenames
        assert "metadata.csv" in filenames

        # Vérifier la présence des stubs COREP
        assert any("corep_c07" in f for f in filenames)
        assert any("corep_c08" in f for f in filenames)


def test_create_export_json(sample_outputs):
    """Test: Export JSON."""
    json_bytes = create_export(
        sample_outputs, format="json", compress=False, include_corep_stubs=False
    )

    assert isinstance(json_bytes, bytes)
    assert len(json_bytes) > 0

    # Vérifier que c'est un JSON valide
    json_data = json.loads(json_bytes.decode("utf-8"))

    assert "metadata" in json_data
    assert "positions" in json_data
    assert "rwa" in json_data
    assert "liquidity" in json_data
    assert "ratios" in json_data


def test_create_export_json_compressed(sample_outputs):
    """Test: Export JSON compressé (gzip)."""
    json_bytes = create_export(
        sample_outputs, format="json", compress=True, include_corep_stubs=False
    )

    assert isinstance(json_bytes, bytes)
    assert len(json_bytes) > 0

    # Vérifier que c'est un gzip valide
    json_str = gzip.decompress(json_bytes).decode("utf-8")
    json_data = json.loads(json_str)

    assert "metadata" in json_data
    assert "positions" in json_data


def test_create_export_json_with_corep_stubs(sample_outputs):
    """Test: Export JSON avec stubs COREP."""
    json_bytes = create_export(
        sample_outputs, format="json", compress=False, include_corep_stubs=True
    )

    json_data = json.loads(json_bytes.decode("utf-8"))

    # Vérifier la présence des stubs COREP
    assert "corep_stubs" in json_data
    assert "COREP C07" in json_data["corep_stubs"]
    assert "COREP C08" in json_data["corep_stubs"]


def test_create_export_invalid_format(sample_outputs):
    """Test: Format invalide."""
    with pytest.raises(ValueError, match="Format non supporté"):
        create_export(sample_outputs, format="invalid", compress=False, include_corep_stubs=False)  # type: ignore


def test_create_export_empty_outputs():
    """Test: Outputs vide."""
    with pytest.raises(ValueError, match="outputs ne peut pas être vide"):
        create_export({}, format="xlsx", compress=False, include_corep_stubs=False)


def test_create_export_missing_positions():
    """Test: Positions manquantes."""
    outputs = {
        "rwa": pd.DataFrame({"rwa": [1000]}),
    }

    with pytest.raises(ValueError, match="positions"):
        create_export(outputs, format="xlsx", compress=False, include_corep_stubs=False)

