"""
Tests unitaires pour le service de gestion des runs (I13).
"""
import json
import tempfile
from datetime import datetime, timedelta

import pytest

from db.base import get_session
from db.models import Exposure, RunComparison, RunLog, SimulationRun
from src.services.run_management_service import (
    add_log,
    cleanup_old_runs,
    clone_run,
    compare_runs,
    compute_checksum,
    delete_run,
    export_run,
    get_run_details,
    import_run,
    list_comparisons,
    list_runs,
    save_comparison,
    toggle_favorite,
    update_notes,
    update_tags,
    validate_run,
)


@pytest.fixture
def sample_run():
    """Crée un run de test."""
    session = get_session()
    
    run = SimulationRun(
        run_id="test_run_001",
        params_hash="test_hash",
        run_date=datetime.utcnow(),
        status="completed",
        total_exposures=100,
        total_notional=1000000,
        config_json='{"seed": 42}',
        duration_seconds=10.5,
        checksum="test_checksum",
        is_favorite=False,
        tags='["test", "sample"]',
    )
    
    session.add(run)
    session.commit()
    
    # Ajouter quelques exposures
    for i in range(10):
        exp = Exposure(
            id=f"exp_{i}",
            run_id="test_run_001",
            product_type="Loan",
            currency="EUR",
            notional=10000,
            ead=9000,
            pd=0.02,
            lgd=0.45,
            entity="EU",
        )
        session.add(exp)
    
    session.commit()
    
    yield run
    
    # Cleanup
    session.query(Exposure).filter_by(run_id="test_run_001").delete()
    session.query(SimulationRun).filter_by(run_id="test_run_001").delete()
    session.commit()


def test_list_runs(sample_run):
    """Test de la liste des runs."""
    runs, total = list_runs(limit=10)
    
    assert total >= 1
    assert any(r['run_id'] == "test_run_001" for r in runs)


def test_list_runs_with_filters(sample_run):
    """Test de la liste avec filtres."""
    # Filtre par statut
    runs, total = list_runs(status_filter="completed", limit=10)
    assert all(r['status'] == "completed" for r in runs)
    
    # Filtre favoris
    runs, total = list_runs(favorites_only=True, limit=10)
    assert all(r['is_favorite'] for r in runs)


def test_get_run_details(sample_run):
    """Test de récupération des détails."""
    details = get_run_details("test_run_001")
    
    assert details is not None
    assert details['run_id'] == "test_run_001"
    assert details['status'] == "completed"
    assert details['total_exposures'] == 100
    assert len(details['stats_by_product']) > 0


def test_get_run_details_not_found():
    """Test avec run inexistant."""
    details = get_run_details("nonexistent_run")
    assert details is None


def test_toggle_favorite(sample_run):
    """Test de toggle favori."""
    # Initial: False
    assert sample_run.is_favorite == False
    
    # Toggle to True
    new_status = toggle_favorite("test_run_001")
    assert new_status == True
    
    # Toggle back to False
    new_status = toggle_favorite("test_run_001")
    assert new_status == False


def test_update_tags(sample_run):
    """Test de mise à jour des tags."""
    new_tags = ["production", "validated"]
    update_tags("test_run_001", new_tags)
    
    details = get_run_details("test_run_001")
    assert details['tags'] == new_tags


def test_update_notes(sample_run):
    """Test de mise à jour des notes."""
    notes = "This is a test run for validation"
    update_notes("test_run_001", notes)
    
    details = get_run_details("test_run_001")
    assert details['notes'] == notes


def test_delete_run(sample_run):
    """Test de suppression de run."""
    # Créer un run temporaire
    session = get_session()
    temp_run = SimulationRun(
        run_id="temp_run",
        params_hash="temp_hash",
        run_date=datetime.utcnow(),
        status="completed",
    )
    session.add(temp_run)
    session.commit()
    
    # Supprimer
    result = delete_run("temp_run")
    assert result == True
    
    # Vérifier suppression
    details = get_run_details("temp_run")
    assert details is None


def test_clone_run(sample_run):
    """Test de clonage de run."""
    modifications = {"seed": 123, "num_exposures": 200}
    new_run_id = clone_run("test_run_001", modifications)
    
    assert new_run_id is not None
    assert new_run_id != "test_run_001"
    
    # Vérifier le nouveau run
    details = get_run_details(new_run_id)
    assert details is not None
    assert details['parent_run_id'] == "test_run_001"
    
    # Cleanup
    delete_run(new_run_id)


def test_compute_checksum(sample_run):
    """Test de calcul de checksum."""
    checksum = compute_checksum("test_run_001")
    
    assert checksum is not None
    assert len(checksum) == 64  # SHA256


def test_validate_run(sample_run):
    """Test de validation de run."""
    validation = validate_run("test_run_001")
    
    assert 'valid' in validation
    assert 'count_valid' in validation
    assert 'checksum_valid' in validation


def test_compare_runs(sample_run):
    """Test de comparaison de runs."""
    # Créer un deuxième run
    session = get_session()
    run2 = SimulationRun(
        run_id="test_run_002",
        params_hash="test_hash_2",
        run_date=datetime.utcnow(),
        status="completed",
        total_exposures=50,
    )
    session.add(run2)
    session.commit()
    
    # Comparer
    comparison = compare_runs(["test_run_001", "test_run_002"])
    
    assert len(comparison['runs_metadata']) == 2
    assert 'exposures_comparison' in comparison
    
    # Cleanup
    delete_run("test_run_002")


def test_save_and_list_comparisons(sample_run):
    """Test de sauvegarde et liste des comparaisons."""
    run_ids = ["test_run_001"]
    comp_id = save_comparison("Test Comparison", run_ids, "Test notes")
    
    assert comp_id is not None
    
    # Lister
    comparisons = list_comparisons()
    assert any(c['id'] == comp_id for c in comparisons)
    
    # Cleanup
    session = get_session()
    session.query(RunComparison).filter_by(id=comp_id).delete()
    session.commit()


def test_export_run_json(sample_run):
    """Test d'export JSON."""
    data_bytes, filename = export_run("test_run_001", format="json")
    
    assert data_bytes is not None
    assert filename.endswith(".json")
    
    # Vérifier contenu
    data = json.loads(data_bytes.decode('utf-8'))
    assert 'metadata' in data
    assert 'exposures' in data
    assert data['metadata']['run_id'] == "test_run_001"


def test_export_run_parquet(sample_run):
    """Test d'export Parquet."""
    data_bytes, filename = export_run("test_run_001", format="parquet")
    
    assert data_bytes is not None
    assert filename.endswith(".parquet")


def test_import_run(sample_run):
    """Test d'import de run."""
    # Export d'abord
    data_bytes, _ = export_run("test_run_001", format="json")
    
    # Sauvegarder dans un fichier temporaire
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp.write(data_bytes.decode('utf-8'))
        tmp_path = tmp.name
    
    # Importer
    new_run_id = import_run(tmp_path)
    
    assert new_run_id is not None
    assert new_run_id.startswith("run_imported_")
    
    # Vérifier
    details = get_run_details(new_run_id)
    assert details is not None
    
    # Cleanup
    import os
    os.unlink(tmp_path)
    delete_run(new_run_id)


def test_cleanup_old_runs():
    """Test de nettoyage des anciens runs."""
    session = get_session()
    
    # Créer un run ancien
    old_run = SimulationRun(
        run_id="old_run",
        params_hash="old_hash",
        run_date=datetime.utcnow() - timedelta(days=60),
        status="completed",
        is_favorite=False,
    )
    session.add(old_run)
    session.commit()
    
    # Dry run
    stats = cleanup_old_runs(days_threshold=30, dry_run=True)
    assert stats['runs_found'] >= 1
    assert "old_run" in stats['run_ids']
    
    # Vérifier que le run existe toujours
    details = get_run_details("old_run")
    assert details is not None
    
    # Vrai nettoyage
    stats = cleanup_old_runs(days_threshold=30, dry_run=False)
    assert stats['runs_deleted'] >= 1
    
    # Vérifier suppression
    details = get_run_details("old_run")
    assert details is None


def test_add_log(sample_run):
    """Test d'ajout de log."""
    add_log("test_run_001", "INFO", "Test log message")
    
    details = get_run_details("test_run_001")
    assert len(details['logs']) > 0
    assert any(log['message'] == "Test log message" for log in details['logs'])

