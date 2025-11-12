"""
Modèles SQLAlchemy pour la persistance.
Tables: configurations, simulations, artifacts, exposures, simulation_runs, balance_sheet_snapshots.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, DateTime, Index, Integer, LargeBinary, Numeric, String, Text

from db.base import Base


class Configuration(Base):
    """
    Table pour stocker les configurations de simulation.
    params_hash = hash des paramètres (clé de cache).
    """
    __tablename__ = "configurations"

    params_hash = Column(String(64), primary_key=True, index=True)
    params_json = Column(Text, nullable=False)  # JSON des paramètres
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Simulation(Base):
    """
    Table pour stocker les résultats de simulation.
    kind: positions, rwa, lcr, nsfr, ratios, etc.
    data_format: parquet, feather, json
    """
    __tablename__ = "simulations"

    id = Column(String(36), primary_key=True)  # UUID
    kind = Column(String(50), nullable=False, index=True)
    params_hash = Column(String(64), nullable=False, index=True)
    data_format = Column(String(20), nullable=False)  # parquet, feather, json
    data_blob = Column(LargeBinary, nullable=True)  # Données sérialisées
    data_path = Column(String(500), nullable=True)  # Chemin fichier si ARTIFACT_STORE=file
    row_count = Column(Integer, nullable=True)  # Nombre de lignes (pour DF)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_simulations_kind_hash", "kind", "params_hash"),
    )


class Artifact(Base):
    """
    Table pour stocker les artifacts (Excel, images, etc.).
    """
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True)  # UUID
    params_hash = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Nom du fichier
    mime_type = Column(String(100), nullable=False)  # application/vnd.ms-excel, image/png, etc.
    data_blob = Column(LargeBinary, nullable=True)  # Données binaires
    data_path = Column(String(500), nullable=True)  # Chemin fichier si ARTIFACT_STORE=file
    size_bytes = Column(Integer, nullable=True)  # Taille en octets
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_artifacts_hash_name", "params_hash", "name"),
    )


# ============================================================================
# I11: Nouveaux modèles pour run_id pipeline
# ============================================================================

class SimulationRun(Base):
    """
    Métadonnées des runs de simulation (I11).
    I13: Ajout champs gestion avancée (duration, checksum, favorite, tags, parent, notes).
    """
    __tablename__ = "simulation_runs"

    run_id = Column(String(36), primary_key=True)  # UUID
    params_hash = Column(String(64), nullable=False, index=True)
    run_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, completed, failed
    total_exposures = Column(Integer, nullable=True)
    total_notional = Column(Numeric(20, 2), nullable=True)
    config_json = Column(Text, nullable=True)  # Snapshot config
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # I13: Nouveaux champs
    duration_seconds = Column(Numeric(10, 2), nullable=True)
    checksum = Column(String(64), nullable=True)
    is_favorite = Column(Boolean, nullable=False, default=False)
    tags = Column(Text, nullable=True)  # JSON array
    parent_run_id = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)


class Exposure(Base):
    """
    Table centrale des expositions par run_id (I11).
    Schéma canonique pour tous les produits.
    """
    __tablename__ = "exposures"

    id = Column(String(36), primary_key=True)  # UUID
    run_id = Column(String(36), nullable=False, index=True)
    product_type = Column(String(50), nullable=False, index=True)  # Loan, Bond, Derivative, etc.
    counterparty_id = Column(String(50), nullable=True)
    booking_date = Column(Date, nullable=True)
    maturity_date = Column(Date, nullable=True)
    currency = Column(String(3), nullable=False)
    notional = Column(Numeric(20, 2), nullable=True)
    ead = Column(Numeric(20, 2), nullable=True)  # Exposure at Default
    pd = Column(Numeric(10, 6), nullable=True)  # Probability of Default
    lgd = Column(Numeric(10, 6), nullable=True)  # Loss Given Default
    ccf = Column(Numeric(10, 6), nullable=True)  # Credit Conversion Factor
    maturity_years = Column(Numeric(10, 2), nullable=True)
    mtm = Column(Numeric(20, 2), nullable=True)  # Mark-to-Market
    desk = Column(String(50), nullable=True)
    entity = Column(String(50), nullable=False, index=True)
    is_retail = Column(Boolean, nullable=False, default=False)
    exposure_class = Column(String(50), nullable=True)  # Corporate, Sovereign, Bank, Retail
    netting_set_id = Column(String(50), nullable=True)  # Pour dérivés
    collateral_value = Column(Numeric(20, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_exposures_run_id", "run_id"),
        Index("ix_exposures_product_type", "product_type"),
        Index("ix_exposures_entity", "entity"),
        Index("ix_exposures_run_product", "run_id", "product_type"),
    )


class BalanceSheetSnapshot(Base):
    """
    Snapshots de bilan par run_id (I11).
    Agrégations simplifiées pour réconciliation.
    """
    __tablename__ = "balance_sheet_snapshots"

    id = Column(String(36), primary_key=True)  # UUID
    run_id = Column(String(36), nullable=False, index=True)
    item_type = Column(String(20), nullable=False)  # asset, liability
    category = Column(String(50), nullable=False)  # loans, bonds, deposits, etc.
    entity = Column(String(50), nullable=False)
    currency = Column(String(3), nullable=False)
    amount = Column(Numeric(20, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_bs_run_id", "run_id"),
        Index("ix_bs_run_entity", "run_id", "entity"),
    )




class ECLResult(Base):
    """
    Table pour stocker les résultats de calcul ECL IFRS 9 (I12).
    """
    __tablename__ = "ecl_results"

    id = Column(String(36), primary_key=True)  # UUID
    run_id = Column(String(50), nullable=False, index=True)
    scenario_id = Column(String(50), nullable=False, index=True)
    exposure_id = Column(String(36), nullable=False, index=True)  # UUID
    stage = Column(String(2), nullable=False)  # S1, S2, S3
    pd_12m = Column(Numeric(10, 6), nullable=True)  # PD 12 mois (%)
    pd_lifetime = Column(Numeric(10, 6), nullable=True)  # PD lifetime (%)
    lgd = Column(Numeric(10, 6), nullable=False)  # LGD utilisée (%)
    ead = Column(Numeric(20, 2), nullable=False)  # EAD (montant)
    ecl_amount = Column(Numeric(20, 2), nullable=False)  # ECL calculée
    ecl_currency = Column(String(3), nullable=False)  # Devise
    segment_id = Column(String(50), nullable=True)  # Segment (Retail/Corporate/...)
    calculation_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_ecl_run_scenario", "run_id", "scenario_id"),
        Index("ix_ecl_stage", "stage"),
    )


class ScenarioOverlay(Base):
    """
    Table pour stocker les scénarios de stress (overlays) pour ECL (I12).
    """
    __tablename__ = "scenario_overlays"

    id = Column(String(36), primary_key=True)  # UUID
    scenario_id = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    pd_shift = Column(Numeric(10, 2), nullable=True)  # Shift PD (bps)
    lgd_floor_by_class = Column(Text, nullable=True)  # JSON: floors LGD par classe
    sicr_threshold_abs = Column(Numeric(10, 2), nullable=True)  # Seuil SICR absolu (bps)
    sicr_threshold_rel = Column(Numeric(10, 2), nullable=True)  # Seuil SICR relatif (%)
    backstop_days = Column(Integer, nullable=True, default=30)  # Backstop jours
    discount_rate_mode = Column(String(20), nullable=True, default='EIR')  # EIR, RFR, Market
    discount_rate_value = Column(Numeric(10, 6), nullable=True)  # Taux si fixe (%)
    horizon_months = Column(Integer, nullable=True, default=12)  # Horizon lifetime (mois)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)




# ============================================================================
# I13: Nouveaux modèles pour gestion avancée des runs
# ============================================================================

class RunLog(Base):
    """
    Logs d'exécution des runs (I13).
    """
    __tablename__ = "run_logs"

    id = Column(String(36), primary_key=True)  # UUID
    run_id = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    level = Column(String(10), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)

    __table_args__ = (
        Index("ix_run_logs_run_id", "run_id"),
    )


class RunComparison(Base):
    """
    Comparaisons sauvegardées entre runs (I13).
    """
    __tablename__ = "run_comparisons"

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(100), nullable=False)
    run_ids = Column(Text, nullable=False)  # JSON array of run_ids
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_run_comparisons_created_at", "created_at"),
    )

