"""
Service de persistance DB-agnostique (I6).
SQLite par défaut, PostgreSQL-ready via DB_URL.
Cache basé sur params_hash pour éviter recalculs.
"""
import hashlib
import json
import os
import uuid
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy.orm import Session

from db.base import SessionLocal, engine
from db.models import Artifact, Base, Simulation

# Créer les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

# Configuration stockage artifacts
ARTIFACT_STORE = os.getenv("ARTIFACT_STORE", "file")
ARTIFACT_PATH = Path(os.getenv("ARTIFACT_PATH", "./data/artifacts"))
if ARTIFACT_STORE == "file":
    ARTIFACT_PATH.mkdir(parents=True, exist_ok=True)


def compute_params_hash(params: dict[str, object]) -> str:
    """
    Calcule un hash SHA256 stable des paramètres.
    Utilisé comme clé de cache.

    Args:
        params: Dictionnaire de paramètres

    Returns:
        Hash hexadécimal (64 caractères)
    """
    # Sérialiser en JSON avec clés triées pour stabilité
    params_str = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(params_str.encode()).hexdigest()


def save_dataframe(
    kind: str,
    params_hash: str,
    df: pd.DataFrame,
    db: Session | None = None
) -> str:
    """
    Sauvegarde un DataFrame avec cache params_hash.
    Format: Parquet (compression snappy).

    Args:
        kind: Type de simulation (positions, rwa, lcr, nsfr, ratios)
        params_hash: Hash des paramètres (clé de cache)
        df: DataFrame à sauvegarder
        db: Session SQLAlchemy (optionnelle)

    Returns:
        ID de la simulation (UUID)
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        sim_id = str(uuid.uuid4())

        if ARTIFACT_STORE == "file":
            # Sauvegarder en fichier Parquet
            file_path = ARTIFACT_PATH / f"{kind}_{params_hash}.parquet"
            table = pa.Table.from_pandas(df)
            pq.write_table(table, file_path, compression="snappy")

            sim = Simulation(
                id=sim_id,
                kind=kind,
                params_hash=params_hash,
                data_format="parquet",
                data_path=str(file_path),
                row_count=len(df),
            )
        else:
            # Sauvegarder en BLOB
            table = pa.Table.from_pandas(df)
            sink = pa.BufferOutputStream()
            pq.write_table(table, sink, compression="snappy")
            data_blob = sink.getvalue().to_pybytes()

            sim = Simulation(
                id=sim_id,
                kind=kind,
                params_hash=params_hash,
                data_format="parquet",
                data_blob=data_blob,
                row_count=len(df),
            )

        db.merge(sim)  # merge = insert or update
        db.commit()
        return sim_id

    finally:
        if close_db:
            db.close()


def load_dataframe(
    kind: str,
    params_hash: str,
    db: Session | None = None
) -> pd.DataFrame | None:
    """
    Charge un DataFrame depuis le cache params_hash.

    Args:
        kind: Type de simulation
        params_hash: Hash des paramètres
        db: Session SQLAlchemy (optionnelle)

    Returns:
        DataFrame si trouvé, None sinon
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        sim = db.query(Simulation).filter(
            Simulation.kind == kind,
            Simulation.params_hash == params_hash
        ).first()

        if not sim:
            return None

        if sim.data_path:
            # Charger depuis fichier
            file_path = Path(sim.data_path)
            if not file_path.exists():
                return None
            table = pq.read_table(file_path)
            result_df: pd.DataFrame = table.to_pandas()
            return result_df
        elif sim.data_blob:
            # Charger depuis BLOB
            table = pq.read_table(pa.BufferReader(sim.data_blob))
            result_df2: pd.DataFrame = table.to_pandas()
            return result_df2

        return None

    finally:
        if close_db:
            db.close()


def save_dict(
    kind: str,
    params_hash: str,
    data: dict[str, object],
    db: Session | None = None
) -> str:
    """
    Sauvegarde un dictionnaire avec cache params_hash.
    Format: JSON.

    Args:
        kind: Type de données
        params_hash: Hash des paramètres
        data: Dictionnaire à sauvegarder
        db: Session SQLAlchemy (optionnelle)

    Returns:
        ID de la simulation (UUID)
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        sim_id = str(uuid.uuid4())
        data_json = json.dumps(data, default=str)

        if ARTIFACT_STORE == "file":
            # Sauvegarder en fichier JSON
            file_path = ARTIFACT_PATH / f"{kind}_{params_hash}.json"
            file_path.write_text(data_json, encoding="utf-8")

            sim = Simulation(
                id=sim_id,
                kind=kind,
                params_hash=params_hash,
                data_format="json",
                data_path=str(file_path),
                row_count=None,
            )
        else:
            # Sauvegarder en BLOB
            sim = Simulation(
                id=sim_id,
                kind=kind,
                params_hash=params_hash,
                data_format="json",
                data_blob=data_json.encode("utf-8"),
                row_count=None,
            )

        db.merge(sim)
        db.commit()
        return sim_id

    finally:
        if close_db:
            db.close()


def load_dict(
    kind: str,
    params_hash: str,
    db: Session | None = None
) -> dict[str, object] | None:
    """
    Charge un dictionnaire depuis le cache params_hash.

    Args:
        kind: Type de données
        params_hash: Hash des paramètres
        db: Session SQLAlchemy (optionnelle)

    Returns:
        Dictionnaire si trouvé, None sinon
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        sim = db.query(Simulation).filter(
            Simulation.kind == kind,
            Simulation.params_hash == params_hash
        ).first()

        if not sim:
            return None

        if sim.data_path:
            # Charger depuis fichier
            file_path = Path(sim.data_path)
            if not file_path.exists():
                return None
            data_json = file_path.read_text(encoding="utf-8")
            result1: dict[str, object] = json.loads(data_json)
            return result1
        elif sim.data_blob:
            # Charger depuis BLOB
            data_json = sim.data_blob.decode("utf-8")
            result2: dict[str, object] = json.loads(data_json)
            return result2

        return None

    finally:
        if close_db:
            db.close()


def save_artifact(
    params_hash: str,
    name: str,
    blob: bytes,
    mime: str,
    db: Session | None = None
) -> str:
    """
    Sauvegarde un artifact binaire (Excel, image, etc.).

    Args:
        params_hash: Hash des paramètres
        name: Nom du fichier
        blob: Données binaires
        mime: Type MIME (application/vnd.ms-excel, image/png, etc.)
        db: Session SQLAlchemy (optionnelle)

    Returns:
        ID de l'artifact (UUID)
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        artifact_id = str(uuid.uuid4())

        if ARTIFACT_STORE == "file":
            # Sauvegarder en fichier
            file_path = ARTIFACT_PATH / f"{params_hash}_{name}"
            file_path.write_bytes(blob)

            artifact = Artifact(
                id=artifact_id,
                params_hash=params_hash,
                name=name,
                mime_type=mime,
                data_path=str(file_path),
                size_bytes=len(blob),
            )
        else:
            # Sauvegarder en BLOB
            artifact = Artifact(
                id=artifact_id,
                params_hash=params_hash,
                name=name,
                mime_type=mime,
                data_blob=blob,
                size_bytes=len(blob),
            )

        db.merge(artifact)
        db.commit()
        return artifact_id

    finally:
        if close_db:
            db.close()


def load_artifact(
    params_hash: str,
    name: str,
    db: Session | None = None
) -> tuple[bytes, str] | None:
    """
    Charge un artifact binaire depuis le cache.

    Args:
        params_hash: Hash des paramètres
        name: Nom du fichier
        db: Session SQLAlchemy (optionnelle)

    Returns:
        Tuple (données binaires, type MIME) si trouvé, None sinon
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        artifact = db.query(Artifact).filter(
            Artifact.params_hash == params_hash,
            Artifact.name == name
        ).first()

        if not artifact:
            return None

        if artifact.data_path:
            # Charger depuis fichier
            file_path = Path(artifact.data_path)
            if not file_path.exists():
                return None
            blob = file_path.read_bytes()
            return (blob, str(artifact.mime_type))
        elif artifact.data_blob:
            # Charger depuis BLOB
            return (bytes(artifact.data_blob), str(artifact.mime_type))

        return None

    finally:
        if close_db:
            db.close()





# ============================================================================
# Utilitaires de listing (I8b)
# ============================================================================


def list_artifacts(limit: int = 50, db: Session | None = None) -> pd.DataFrame:
    """
    Liste les artifacts persistés (I8b).

    Args:
        limit: Nombre maximum d'artifacts à retourner
        db: Session SQLAlchemy (optionnelle)

    Returns:
        DataFrame avec colonnes: artifact_id, params_hash, name, mime_type, size_bytes, created_at
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Requête SQL pour lister les artifacts
        artifacts = (
            db.query(Artifact)
            .order_by(Artifact.created_at.desc())
            .limit(limit)
            .all()
        )

        # Convertir en DataFrame
        data = []
        for artifact in artifacts:
            # Calculer la taille
            if artifact.blob_path:
                # Fichier sur disque
                file_path = ARTIFACT_PATH / artifact.blob_path
                size_bytes = file_path.stat().st_size if file_path.exists() else 0
            elif artifact.blob_data:
                # Blob en DB
                size_bytes = len(artifact.blob_data)
            else:
                size_bytes = 0

            data.append({
                "artifact_id": artifact.artifact_id,
                "params_hash": artifact.params_hash,
                "name": artifact.name,
                "mime_type": artifact.mime_type,
                "size_bytes": size_bytes,
                "created_at": artifact.created_at,
            })

        return pd.DataFrame(data)

    finally:
        if close_db:
            db.close()


def list_configurations(limit: int = 50, db: Session | None = None) -> pd.DataFrame:
    """
    Liste les configurations persistées (I8b).

    Args:
        limit: Nombre maximum de configurations à retourner
        db: Session SQLAlchemy (optionnelle)

    Returns:
        DataFrame avec colonnes: config_id, params_hash, name, num_positions, seed, created_at
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Requête SQL pour lister les simulations (configurations)
        # Note: On utilise la table simulations pour stocker les configurations
        # avec kind="configuration"
        simulations = (
            db.query(Simulation)
            .filter(Simulation.kind == "configuration")
            .order_by(Simulation.created_at.desc())
            .limit(limit)
            .all()
        )

        # Convertir en DataFrame
        data = []
        for sim in simulations:
            # Charger les paramètres depuis data_parquet
            try:
                if sim.data_parquet:
                    import io
                    parquet_bytes = sim.data_parquet
                    config_df = pd.read_parquet(io.BytesIO(parquet_bytes))
                    
                    # Extraire les paramètres
                    if not config_df.empty:
                        config_dict = config_df.iloc[0].to_dict()
                        num_positions = config_dict.get("num_positions", 0)
                        seed = config_dict.get("seed", 0)
                        name = config_dict.get("name", "Sans nom")
                    else:
                        num_positions = 0
                        seed = 0
                        name = "Sans nom"
                else:
                    num_positions = 0
                    seed = 0
                    name = "Sans nom"
            except Exception:
                num_positions = 0
                seed = 0
                name = "Sans nom"

            data.append({
                "config_id": sim.simulation_id,
                "params_hash": sim.params_hash,
                "name": name,
                "num_positions": num_positions,
                "seed": seed,
                "created_at": sim.created_at,
            })

        return pd.DataFrame(data)

    finally:
        if close_db:
            db.close()

