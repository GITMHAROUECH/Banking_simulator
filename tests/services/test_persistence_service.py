"""
Tests pour le service de persistance (I6).
Vérifie round-trip DF/dict/blob et stabilité du hash.
"""
import pandas as pd
import pytest

from src.services.persistence_service import (
    compute_params_hash,
    save_dataframe,
    load_dataframe,
    save_dict,
    load_dict,
    save_artifact,
    load_artifact,
)


def test_compute_params_hash_stable():
    """Le hash doit être stable pour les mêmes paramètres."""
    params1 = {"a": 1, "b": 2, "c": [3, 4, 5]}
    params2 = {"c": [3, 4, 5], "a": 1, "b": 2}  # Ordre différent
    
    hash1 = compute_params_hash(params1)
    hash2 = compute_params_hash(params2)
    
    assert hash1 == hash2, "Hash doit être stable indépendamment de l'ordre"
    assert len(hash1) == 64, "Hash SHA256 doit faire 64 caractères"


def test_compute_params_hash_different():
    """Le hash doit être différent pour des paramètres différents."""
    params1 = {"a": 1, "b": 2}
    params2 = {"a": 1, "b": 3}
    
    hash1 = compute_params_hash(params1)
    hash2 = compute_params_hash(params2)
    
    assert hash1 != hash2, "Hash doit être différent pour des paramètres différents"


def test_dataframe_round_trip():
    """Round-trip DataFrame: save puis load."""
    # Créer un DataFrame de test
    df = pd.DataFrame({
        'position_id': ['P1', 'P2', 'P3'],
        'ead': [100.0, 200.0, 300.0],
        'rwa': [50.0, 100.0, 150.0],
    })
    
    params_hash = "test_hash_df_001"
    
    # Sauvegarder
    sim_id = save_dataframe("test_positions", params_hash, df)
    assert sim_id is not None
    
    # Charger
    loaded_df = load_dataframe("test_positions", params_hash)
    assert loaded_df is not None
    assert len(loaded_df) == 3
    assert list(loaded_df.columns) == ['position_id', 'ead', 'rwa']
    assert loaded_df['ead'].sum() == 600.0


def test_dataframe_not_found():
    """load_dataframe doit retourner None si non trouvé."""
    loaded_df = load_dataframe("nonexistent_kind", "nonexistent_hash")
    assert loaded_df is None


def test_dict_round_trip():
    """Round-trip dict: save puis load."""
    data = {
        'cet1_ratio': 0.15,
        'tier1_ratio': 0.18,
        'total_capital_ratio': 0.20,
        'leverage_ratio': 0.05,
    }
    
    params_hash = "test_hash_dict_001"
    
    # Sauvegarder
    sim_id = save_dict("test_ratios", params_hash, data)
    assert sim_id is not None
    
    # Charger
    loaded_dict = load_dict("test_ratios", params_hash)
    assert loaded_dict is not None
    assert loaded_dict['cet1_ratio'] == 0.15
    assert loaded_dict['tier1_ratio'] == 0.18
    assert loaded_dict['total_capital_ratio'] == 0.20
    assert loaded_dict['leverage_ratio'] == 0.05


def test_dict_not_found():
    """load_dict doit retourner None si non trouvé."""
    loaded_dict = load_dict("nonexistent_kind", "nonexistent_hash")
    assert loaded_dict is None


def test_artifact_round_trip():
    """Round-trip artifact: save puis load."""
    # Créer un artifact de test (simule un fichier Excel)
    blob = b"Fake Excel Content: " + b"x" * 1000
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    params_hash = "test_hash_artifact_001"
    name = "export.xlsx"
    
    # Sauvegarder
    artifact_id = save_artifact(params_hash, name, blob, mime)
    assert artifact_id is not None
    
    # Charger
    loaded_artifact = load_artifact(params_hash, name)
    assert loaded_artifact is not None
    loaded_blob, loaded_mime = loaded_artifact
    assert loaded_blob == blob
    assert loaded_mime == mime


def test_artifact_not_found():
    """load_artifact doit retourner None si non trouvé."""
    loaded_artifact = load_artifact("nonexistent_hash", "nonexistent.xlsx")
    assert loaded_artifact is None


def test_dataframe_cache_hit():
    """Vérifier que le cache fonctionne (2ème load retourne les mêmes données)."""
    df = pd.DataFrame({
        'position_id': ['P1', 'P2'],
        'ead': [100.0, 200.0],
    })
    
    params_hash = "test_hash_cache_001"
    
    # 1er save
    save_dataframe("test_cache", params_hash, df)
    
    # 1er load
    loaded_df1 = load_dataframe("test_cache", params_hash)
    assert loaded_df1 is not None
    assert len(loaded_df1) == 2
    
    # 2ème load (cache hit)
    loaded_df2 = load_dataframe("test_cache", params_hash)
    assert loaded_df2 is not None
    assert len(loaded_df2) == 2
    assert loaded_df1.equals(loaded_df2)


def test_multiple_kinds_same_hash():
    """Différents 'kind' avec le même hash ne doivent pas se confondre."""
    params_hash = "shared_hash_001"
    
    df1 = pd.DataFrame({'col': [1, 2, 3]})
    df2 = pd.DataFrame({'col': [4, 5, 6]})
    
    save_dataframe("kind_a", params_hash, df1)
    save_dataframe("kind_b", params_hash, df2)
    
    loaded_a = load_dataframe("kind_a", params_hash)
    loaded_b = load_dataframe("kind_b", params_hash)
    
    assert loaded_a is not None
    assert loaded_b is not None
    assert loaded_a['col'].sum() == 6  # 1+2+3
    assert loaded_b['col'].sum() == 15  # 4+5+6

