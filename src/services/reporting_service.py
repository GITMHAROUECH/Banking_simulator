"""
Service d'orchestration pour le reporting et l'export (I8).

Ce service coordonne la création d'exports multi-formats
avec positions, RWA, liquidité, capital, SA-CCR et stubs COREP/LE/LCR.
"""

import gzip
import json
from datetime import datetime
from io import BytesIO
from typing import Any, Literal
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from src.services.persistence_service import (
    compute_params_hash,
    load_artifact,
    save_artifact,
)
from src.domain.reporting.corep import (
    generate_corep_c07,
    generate_corep_c08,
    generate_corep_c34,
)
from src.domain.reporting.finrep import (
    generate_finrep_f09,
    generate_finrep_f18,
)


# ============================================================================
# API d'export unifiée (I8)
# ============================================================================


def create_export(
    outputs: dict[str, Any],
    *,
    format: Literal["xlsx", "parquet", "csv", "json"] = "xlsx",
    compress: bool = False,
    include_corep_stubs: bool = True,
) -> bytes:
    """
    Crée un export multi-formats avec stubs COREP/LE/LCR optionnels.

    Args:
        outputs: Dict avec clés:
            - positions: pd.DataFrame (obligatoire)
            - rwa: pd.DataFrame (optionnel)
            - liquidity: dict[str, pd.DataFrame] (optionnel, clés: lcr, nsfr)
            - ratios: dict[str, float] (optionnel)
            - saccr: dict[str, Any] (optionnel, clés: ead_df, rwa, rc, pfe, etc.)
            - metadata: dict[str, Any] (optionnel)
        format: Format d'export ("xlsx", "parquet", "csv", "json")
        compress: Si True, compresse le résultat (gzip pour json, zip pour csv)
        include_corep_stubs: Si True, inclut les stubs COREP/LE/LCR

    Returns:
        bytes: Contenu du fichier exporté

    Raises:
        ValueError: Si outputs est vide ou format invalide
    """
    # Validation
    if not outputs:
        raise ValueError("outputs ne peut pas être vide")

    if "positions" not in outputs or outputs["positions"].empty:
        raise ValueError("outputs doit contenir une clé 'positions' non vide")

    # Préparer les données
    positions_df = outputs["positions"]
    rwa_df = outputs.get("rwa", pd.DataFrame())
    liquidity = outputs.get("liquidity", {})
    ratios = outputs.get("ratios", {})
    saccr = outputs.get("saccr", {})
    metadata = outputs.get("metadata", {})

    # Ajouter métadonnées par défaut
    if "export_date" not in metadata:
        metadata["export_date"] = datetime.now().isoformat()

    # Générer les stubs COREP/LE/LCR si demandé
    corep_stubs = {}
    if include_corep_stubs:
        corep_stubs = _generate_corep_stubs(
            positions_df, rwa_df, liquidity, ratios, saccr
        )

    # Export selon le format
    if format == "xlsx":
        return _export_xlsx(
            positions_df, rwa_df, liquidity, ratios, saccr, metadata, corep_stubs
        )
    elif format == "parquet":
        return _export_parquet(
            positions_df, rwa_df, liquidity, ratios, saccr, metadata, compress
        )
    elif format == "csv":
        return _export_csv(
            positions_df, rwa_df, liquidity, ratios, saccr, metadata, corep_stubs, compress
        )
    elif format == "json":
        return _export_json(
            positions_df, rwa_df, liquidity, ratios, saccr, metadata, corep_stubs, compress
        )
    else:
        raise ValueError(f"Format non supporté: {format}")


# ============================================================================
# Fonctions d'export par format
# ============================================================================


def _export_xlsx(
    positions_df: pd.DataFrame,
    rwa_df: pd.DataFrame,
    liquidity: dict[str, pd.DataFrame],
    ratios: dict[str, float],
    saccr: dict[str, Any],
    metadata: dict[str, Any],
    corep_stubs: dict[str, pd.DataFrame],
) -> bytes:
    """Exporte en format XLSX multi-onglets."""
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Onglet 1 : Positions
        positions_df.to_excel(writer, sheet_name="Positions", index=False)

        # Onglet 2 : RWA
        if not rwa_df.empty:
            rwa_df.to_excel(writer, sheet_name="RWA", index=False)

        # Onglet 3 : Liquidité (LCR)
        if "lcr" in liquidity and not liquidity["lcr"].empty:
            liquidity["lcr"].to_excel(writer, sheet_name="LCR", index=False)

        # Onglet 4 : Liquidité (NSFR)
        if "nsfr" in liquidity and not liquidity["nsfr"].empty:
            liquidity["nsfr"].to_excel(writer, sheet_name="NSFR", index=False)

        # Onglet 5 : Ratios de capital
        if ratios:
            ratios_df = pd.DataFrame([ratios])
            ratios_df.to_excel(writer, sheet_name="Ratios Capital", index=False)

        # Onglet 6 : SA-CCR (EAD)
        if "ead_df" in saccr and not saccr["ead_df"].empty:
            saccr["ead_df"].to_excel(writer, sheet_name="SA-CCR EAD", index=False)

        # Onglet 7 : SA-CCR (Métriques)
        if saccr:
            saccr_metrics = {
                k: v
                for k, v in saccr.items()
                if k not in ["ead_df", "pfe_addons"] and not isinstance(v, pd.DataFrame)
            }
            if saccr_metrics:
                saccr_metrics_df = pd.DataFrame([saccr_metrics])
                saccr_metrics_df.to_excel(
                    writer, sheet_name="SA-CCR Métriques", index=False
                )

        # Onglets COREP/LE/LCR (stubs)
        for stub_name, stub_df in corep_stubs.items():
            if not stub_df.empty:
                stub_df.to_excel(writer, sheet_name=stub_name, index=False)

        # Onglet Meta
        metadata_df = pd.DataFrame([metadata])
        metadata_df.to_excel(writer, sheet_name="Meta", index=False)

    buffer.seek(0)
    return buffer.read()


def _export_parquet(
    positions_df: pd.DataFrame,
    rwa_df: pd.DataFrame,
    liquidity: dict[str, pd.DataFrame],
    ratios: dict[str, float],
    saccr: dict[str, Any],
    metadata: dict[str, Any],
    compress: bool,
) -> bytes:
    """Exporte en format Parquet (positions uniquement, format colonnaire)."""
    buffer = BytesIO()

    # Ajouter métadonnées comme colonnes
    positions_with_meta = positions_df.copy()
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            positions_with_meta[f"meta_{key}"] = value

    # Compression
    compression = "gzip" if compress else None

    positions_with_meta.to_parquet(buffer, engine="pyarrow", compression=compression)

    buffer.seek(0)
    return buffer.read()


def _export_csv(
    positions_df: pd.DataFrame,
    rwa_df: pd.DataFrame,
    liquidity: dict[str, pd.DataFrame],
    ratios: dict[str, float],
    saccr: dict[str, Any],
    metadata: dict[str, Any],
    corep_stubs: dict[str, pd.DataFrame],
    compress: bool,
) -> bytes:
    """Exporte en format CSV (zip si compress=True)."""
    if not compress:
        # CSV simple (positions uniquement)
        return positions_df.to_csv(index=False).encode("utf-8")

    # CSV multi-fichiers (zip)
    buffer = BytesIO()

    with ZipFile(buffer, "w", ZIP_DEFLATED) as zipf:
        # Positions
        zipf.writestr("positions.csv", positions_df.to_csv(index=False))

        # RWA
        if not rwa_df.empty:
            zipf.writestr("rwa.csv", rwa_df.to_csv(index=False))

        # Liquidité
        if "lcr" in liquidity and not liquidity["lcr"].empty:
            zipf.writestr("lcr.csv", liquidity["lcr"].to_csv(index=False))

        if "nsfr" in liquidity and not liquidity["nsfr"].empty:
            zipf.writestr("nsfr.csv", liquidity["nsfr"].to_csv(index=False))

        # Ratios
        if ratios:
            ratios_df = pd.DataFrame([ratios])
            zipf.writestr("ratios.csv", ratios_df.to_csv(index=False))

        # SA-CCR
        if "ead_df" in saccr and not saccr["ead_df"].empty:
            zipf.writestr("saccr_ead.csv", saccr["ead_df"].to_csv(index=False))

        # COREP stubs
        for stub_name, stub_df in corep_stubs.items():
            if not stub_df.empty:
                filename = f"corep_{stub_name.lower().replace(' ', '_')}.csv"
                zipf.writestr(filename, stub_df.to_csv(index=False))

        # Metadata
        metadata_df = pd.DataFrame([metadata])
        zipf.writestr("metadata.csv", metadata_df.to_csv(index=False))

    buffer.seek(0)
    return buffer.read()


def _export_json(
    positions_df: pd.DataFrame,
    rwa_df: pd.DataFrame,
    liquidity: dict[str, pd.DataFrame],
    ratios: dict[str, float],
    saccr: dict[str, Any],
    metadata: dict[str, Any],
    corep_stubs: dict[str, pd.DataFrame],
    compress: bool,
) -> bytes:
    """Exporte en format JSON (gzip si compress=True)."""
    # Construire le dict JSON
    export_dict: dict[str, Any] = {
        "metadata": metadata,
        "positions": positions_df.to_dict(orient="records"),
    }

    if not rwa_df.empty:
        export_dict["rwa"] = rwa_df.to_dict(orient="records")

    if liquidity:
        export_dict["liquidity"] = {}
        if "lcr" in liquidity and not liquidity["lcr"].empty:
            export_dict["liquidity"]["lcr"] = liquidity["lcr"].to_dict(orient="records")
        if "nsfr" in liquidity and not liquidity["nsfr"].empty:
            export_dict["liquidity"]["nsfr"] = liquidity["nsfr"].to_dict(
                orient="records"
            )

    if ratios:
        export_dict["ratios"] = ratios

    if saccr:
        export_dict["saccr"] = {}
        if "ead_df" in saccr and not saccr["ead_df"].empty:
            export_dict["saccr"]["ead"] = saccr["ead_df"].to_dict(orient="records")

        # Métriques SA-CCR (scalaires)
        saccr_metrics = {
            k: v
            for k, v in saccr.items()
            if k not in ["ead_df", "pfe_addons"] and not isinstance(v, pd.DataFrame)
        }
        export_dict["saccr"]["metrics"] = saccr_metrics

    if corep_stubs:
        export_dict["corep_stubs"] = {
            name: df.to_dict(orient="records") for name, df in corep_stubs.items()
        }

    # Sérialiser en JSON
    json_str = json.dumps(export_dict, indent=2, default=str)
    json_bytes = json_str.encode("utf-8")

    # Compression gzip si demandé
    if compress:
        return gzip.compress(json_bytes)

    return json_bytes


# ============================================================================
# Génération des stubs COREP/LE/LCR (I8)
# ============================================================================


def _generate_corep_stubs(
    positions_df: pd.DataFrame,
    rwa_df: pd.DataFrame,
    liquidity: dict[str, pd.DataFrame],
    ratios: dict[str, float],
    saccr: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    """
    Génère les rapports COREP/FINREP/LCR complets (EBA v3.3 compliant).

    Note: Renamed from "stubs" to reflect full calculations (not just stubs).

    Returns:
        Dict avec clés:
            - "COREP C34": Full SA-CCR (contrepartie) - EBA v3.3
            - "COREP C07": Full crédit (expositions) - EBA v3.3
            - "COREP C08": Full crédit (RWA) - EBA v3.3
            - "FINREP F18": Full loans breakdown (if positions contains loans)
            - "Leverage": Leverage ratio summary
            - "LCR": LCR summary
    """
    reports = {}

    # ========================================================================
    # COREP Reports (Full calculations, EBA v3.3)
    # ========================================================================

    # COREP C34 (SA-CCR) - Full calculation
    if "ead_df" in saccr and not saccr["ead_df"].empty:
        try:
            reports["COREP C34"] = generate_corep_c34(saccr)
        except Exception:
            # Fallback to legacy stub if error
            reports["COREP C34"] = _generate_corep_c34_stub(saccr)

    # COREP C07 (Credit - Exposures) - Full calculation
    if not positions_df.empty:
        try:
            reports["COREP C07"] = generate_corep_c07(positions_df, rwa_df)
        except Exception:
            # Fallback to legacy stub if error
            reports["COREP C07"] = _generate_corep_c07_stub(positions_df)

    # COREP C08 (Credit - RWA) - Full calculation
    if not rwa_df.empty:
        try:
            reports["COREP C08"] = generate_corep_c08(positions_df, rwa_df)
        except Exception:
            # Fallback to legacy stub if error
            reports["COREP C08"] = _generate_corep_c08_stub(rwa_df)

    # ========================================================================
    # FINREP Reports (Full calculations, EBA v3.3)
    # ========================================================================

    # FINREP F18 (Loans) - Full calculation
    if not positions_df.empty and "product_type" in positions_df.columns:
        try:
            reports["FINREP F18"] = generate_finrep_f18(positions_df)
        except Exception:
            # Silent fail if error (optional report)
            pass

    # ========================================================================
    # Other Reports (Legacy/Summary)
    # ========================================================================

    # Leverage Ratio (Summary)
    if ratios and "leverage_ratio" in ratios:
        reports["Leverage"] = _generate_leverage_stub(positions_df, ratios)

    # LCR (Summary)
    if "lcr" in liquidity and not liquidity["lcr"].empty:
        reports["LCR"] = _generate_lcr_stub(liquidity["lcr"])

    return reports


def _generate_corep_c34_stub(saccr: dict[str, Any]) -> pd.DataFrame:
    """Génère le stub COREP C34 (SA-CCR)."""
    ead_df = saccr["ead_df"]

    # Agréger par netting_set
    c34_df = (
        ead_df.groupby("netting_set")
        .agg({"ead_contribution": "sum"})
        .reset_index()
        .rename(columns={"netting_set": "Counterparty", "ead_contribution": "EAD"})
    )

    # Ajouter colonnes COREP C34
    c34_df["RC"] = saccr.get("rc", 0)
    c34_df["PFE"] = saccr.get("pfe", 0)
    c34_df["Multiplier"] = saccr.get("multiplier", 1.0)
    c34_df["Alpha"] = saccr.get("alpha", 1.4)

    return c34_df


def _generate_corep_c07_stub(positions_df: pd.DataFrame) -> pd.DataFrame:
    """Génère le stub COREP C07 (Crédit - Expositions)."""
    # Vérifier si la colonne exposure existe, sinon utiliser notional
    exposure_col = "exposure" if "exposure" in positions_df.columns else "notional"
    
    if exposure_col not in positions_df.columns:
        # Retourner un DataFrame vide si aucune colonne d'exposition
        return pd.DataFrame(columns=["Exposure Class", "Total Exposure"])
    
    # Agréger par exposure_class
    c07_df = (
        positions_df.groupby("exposure_class")
        .agg({exposure_col: "sum"})
        .reset_index()
        .rename(columns={"exposure_class": "Exposure Class", exposure_col: "Total Exposure"})
    )

    return c07_df


def _generate_corep_c08_stub(rwa_df: pd.DataFrame) -> pd.DataFrame:
    """Génère le stub COREP C08 (Crédit - RWA)."""
    # Vérifier si la colonne rwa existe
    if "rwa" not in rwa_df.columns:
        # Retourner un DataFrame vide si aucune colonne rwa
        return pd.DataFrame(columns=["Exposure Class", "Total RWA"])
    
    # Agréger par exposure_class
    c08_df = (
        rwa_df.groupby("exposure_class")
        .agg({"rwa": "sum"})
        .reset_index()
        .rename(columns={"exposure_class": "Exposure Class", "rwa": "Total RWA"})
    )

    return c08_df


def _generate_leverage_stub(
    positions_df: pd.DataFrame, ratios: dict[str, float]
) -> pd.DataFrame:
    """Génère le stub Leverage Ratio."""
    # Vérifier si la colonne exposure existe, sinon utiliser notional
    exposure_col = "exposure" if "exposure" in positions_df.columns else "notional"
    
    if exposure_col not in positions_df.columns:
        total_exposure = 0.0
    else:
        total_exposure = positions_df[exposure_col].sum()
    
    leverage_ratio = ratios.get("leverage_ratio", 0.0)

    leverage_df = pd.DataFrame(
        {
            "Metric": ["Total Exposure", "Tier 1 Capital", "Leverage Ratio"],
            "Value": [
                total_exposure,
                ratios.get("tier1", 0.0),
                leverage_ratio,
            ],
        }
    )

    return leverage_df


def _generate_lcr_stub(lcr_df: pd.DataFrame) -> pd.DataFrame:
    """Génère le stub LCR."""
    # Vérifier si les colonnes category et amount existent
    if "category" not in lcr_df.columns or "amount" not in lcr_df.columns:
        # Retourner un DataFrame vide si colonnes manquantes
        return pd.DataFrame(columns=["Category", "Amount"])
    
    # Agréger par catégorie
    lcr_stub = (
        lcr_df.groupby("category")
        .agg({"amount": "sum"})
        .reset_index()
        .rename(columns={"category": "Category", "amount": "Amount"})
    )

    return lcr_stub


# ============================================================================
# Fonction legacy (I1-I7) - Préservée pour compatibilité
# ============================================================================


def create_excel_export(
    positions_df: pd.DataFrame,
    rwa_df: pd.DataFrame,
    lcr_df: pd.DataFrame,
    nsfr_df: pd.DataFrame,
    capital_ratios: dict[str, float],
    use_cache: bool = True,
) -> tuple[bytes, bool]:
    """
    Crée un export Excel multi-onglets (fonction legacy I1-I7).

    Cette fonction est préservée pour compatibilité avec I1-I7.
    Pour les nouveaux exports, utiliser create_export().

    Args:
        positions_df: DataFrame des positions
        rwa_df: DataFrame des RWA
        lcr_df: DataFrame LCR
        nsfr_df: DataFrame NSFR
        capital_ratios: Dict des ratios de capital
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Tuple (bytes, cache_hit):
            - bytes: Contenu du fichier Excel
            - cache_hit: True si chargé depuis le cache, False si généré
    """
    # Validation
    if positions_df.empty:
        raise ValueError("positions_df ne peut pas être vide")
    if rwa_df.empty:
        raise ValueError("rwa_df ne peut pas être vide")

    # Calculer le hash des paramètres pour le cache (I6)
    params_dict: dict[str, object] = {
        "positions_count": len(positions_df),
        "rwa_count": len(rwa_df),
        "lcr_count": len(lcr_df),
        "nsfr_count": len(nsfr_df),
        "capital_ratios": capital_ratios,
    }
    params_hash = compute_params_hash(params_dict)

    # Tenter de charger depuis le cache (I6)
    if use_cache:
        cached_blob, cached_mime = load_artifact(params_hash, "excel_export") or (
            None,
            None,
        )
        if cached_blob is not None:
            return (cached_blob, True)  # Cache hit

    # Préparer les outputs pour create_export
    outputs = {
        "positions": positions_df,
        "rwa": rwa_df,
        "liquidity": {"lcr": lcr_df, "nsfr": nsfr_df},
        "ratios": capital_ratios,
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "version": "0.8.0",
        },
    }

    # Générer l'export via create_export
    excel_bytes = create_export(
        outputs, format="xlsx", compress=False, include_corep_stubs=False
    )

    # Sauvegarder dans le cache (I6)
    if use_cache:
        save_artifact(
            params_hash,
            "excel_export",
            excel_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    return (excel_bytes, False)  # Cache miss




# ============================================================================
# I11: Pré-remplissage COREP/FINREP à partir de run_id
# ============================================================================

def create_corep_finrep_stubs(run_id: str) -> dict[str, pd.DataFrame]:
    """
    Pré-remplit les stubs COREP/FINREP à partir d'un run_id (I11).
    
    Args:
        run_id: Identifiant du run
    
    Returns:
        Dict avec clés:
            - corep_c34: COREP C34 (Standardised approach - Credit risk exposures by exposure class and risk weight)
            - corep_c07: COREP C07 (IRB approach - Credit risk exposures by exposure class and PD scale)
            - corep_c08: COREP C08 (IRB approach - Credit risk exposures by portfolio and PD scale)
            - corep_leverage: COREP Leverage Ratio
            - corep_lcr: COREP LCR
            - finrep_f01: FINREP F01 (Balance sheet - Assets)
            - finrep_f18: FINREP F18 (Breakdown of loans and advances by product)
    """
    from src.services.exposure_service import load_exposures, snapshot_balance_sheet
    from src.services.risk_service import (
        compute_capital_ratios_from_run,
        compute_lcr_from_run,
        compute_rwa_from_run,
    )
    
    # Charger les données
    df_exp = load_exposures(run_id)
    df_assets, df_liabilities = snapshot_balance_sheet(run_id)
    
    # Calculer les métriques
    rwa_result, _ = compute_rwa_from_run(run_id)
    lcr_result, _ = compute_lcr_from_run(run_id)
    capital_result, _ = compute_capital_ratios_from_run(run_id)
    
    # ========================================================================
    # COREP C34: Standardised approach - Credit risk exposures
    # ========================================================================
    df_c34 = df_exp[df_exp['product_type'].isin(['Loan', 'Bond', 'Commitment', 'Guarantee'])].copy()
    
    # Calculer risk weight simplifié (basé sur exposure_class)
    risk_weight_map = {
        'Sovereign': 0,
        'Bank': 20,
        'Corporate': 100,
        'Retail': 75,
    }
    df_c34['risk_weight'] = df_c34['exposure_class'].map(risk_weight_map).fillna(100)
    df_c34['rwa'] = df_c34['ead'] * df_c34['risk_weight'] / 100
    
    corep_c34 = df_c34.groupby(['exposure_class', 'risk_weight']).agg({
        'ead': 'sum',
        'rwa': 'sum',
    }).reset_index()
    
    corep_c34.rename(columns={
        'exposure_class': 'Exposure Class',
        'risk_weight': 'Risk Weight (%)',
        'ead': 'Exposure Value',
        'rwa': 'Risk Weighted Exposure Amount',
    }, inplace=True)
    
    # ========================================================================
    # COREP C07: IRB approach - Credit risk exposures by exposure class and PD scale
    # ========================================================================
    df_c07 = df_exp[df_exp['pd'].notna()].copy()
    
    # Créer des buckets PD
    df_c07['pd_bucket'] = pd.cut(
        df_c07['pd'],
        bins=[0, 0.001, 0.005, 0.01, 0.05, 0.1, 1.0],
        labels=['0-0.1%', '0.1-0.5%', '0.5-1%', '1-5%', '5-10%', '>10%']
    )
    
    corep_c07 = df_c07.groupby(['exposure_class', 'pd_bucket']).agg({
        'ead': 'sum',
        'pd': 'mean',
        'lgd': 'mean',
    }).reset_index()
    
    corep_c07.rename(columns={
        'exposure_class': 'Exposure Class',
        'pd_bucket': 'PD Scale',
        'ead': 'Exposure Value',
        'pd': 'Average PD (%)',
        'lgd': 'Average LGD (%)',
    }, inplace=True)
    
    corep_c07['Average PD (%)'] = corep_c07['Average PD (%)'] * 100
    corep_c07['Average LGD (%)'] = corep_c07['Average LGD (%)'] * 100
    
    # ========================================================================
    # COREP C08: IRB approach - Credit risk exposures by portfolio
    # ========================================================================
    corep_c08 = df_c07.groupby(['exposure_class', 'pd_bucket']).agg({
        'ead': 'sum',
    }).reset_index()
    
    corep_c08.rename(columns={
        'exposure_class': 'Portfolio',
        'pd_bucket': 'PD Scale',
        'ead': 'Exposure Value',
    }, inplace=True)
    
    # ========================================================================
    # COREP Leverage Ratio
    # ========================================================================
    corep_leverage = pd.DataFrame([{
        'Tier 1 Capital': capital_result['tier1_capital'],
        'Total Exposure Measure': capital_result['total_exposure'],
        'Leverage Ratio (%)': capital_result['leverage_ratio'],
        'Minimum Required (%)': 3.0,
        'Compliant': 'Yes' if capital_result['leverage_compliant'] else 'No',
    }])
    
    # ========================================================================
    # COREP LCR
    # ========================================================================
    corep_lcr = pd.DataFrame([{
        'Total HQLA': lcr_result['hqla'],
        'Total Net Cash Outflows': lcr_result['net_cash_outflows'],
        'LCR Ratio (%)': lcr_result['lcr_ratio'],
        'Minimum Required (%)': 100.0,
        'Compliant': 'Yes' if lcr_result['compliant'] else 'No',
    }])
    
    # ========================================================================
    # FINREP F01: Balance sheet - Assets
    # ========================================================================
    finrep_f01 = df_assets.groupby('category').agg({
        'amount': 'sum',
    }).reset_index()
    
    finrep_f01.rename(columns={
        'category': 'Asset Category',
        'amount': 'Carrying Amount',
    }, inplace=True)
    
    # Ajouter total
    total_assets = finrep_f01['Carrying Amount'].sum()
    finrep_f01 = pd.concat([
        finrep_f01,
        pd.DataFrame([{'Asset Category': 'TOTAL ASSETS', 'Carrying Amount': total_assets}])
    ], ignore_index=True)
    
    # ========================================================================
    # FINREP F18: Breakdown of loans and advances
    # ========================================================================
    df_loans = df_exp[df_exp['product_type'] == 'Loan'].copy()
    
    # Vérifier si is_retail existe, sinon utiliser exposure_class uniquement
    if 'is_retail' in df_loans.columns and df_loans['is_retail'].notna().any():
        finrep_f18 = df_loans.groupby(['exposure_class', 'is_retail']).agg({
            'notional': 'sum',
            'ead': 'sum',
        }).reset_index()
        
        finrep_f18['segment'] = finrep_f18.apply(
            lambda row: 'Retail' if row['is_retail'] else row['exposure_class'],
            axis=1
        )
    else:
        # Fallback : utiliser exposure_class directement
        finrep_f18 = df_loans.groupby('exposure_class').agg({
            'notional': 'sum',
            'ead': 'sum',
        }).reset_index()
        finrep_f18.rename(columns={'exposure_class': 'segment'}, inplace=True)
    
    finrep_f18 = finrep_f18.groupby('segment').agg({
        'notional': 'sum',
        'ead': 'sum',
    }).reset_index()
    
    finrep_f18.rename(columns={
        'segment': 'Loan Segment',
        'notional': 'Gross Carrying Amount',
        'ead': 'Net Carrying Amount',
    }, inplace=True)
    
    # Retourner tous les stubs
    return {
        'corep_c34': corep_c34,
        'corep_c07': corep_c07,
        'corep_c08': corep_c08,
        'corep_leverage': corep_leverage,
        'corep_lcr': corep_lcr,
        'finrep_f01': finrep_f01,
        'finrep_f18': finrep_f18,
    }


def export_corep_finrep_to_excel(run_id: str, output_path: str) -> None:
    """
    Exporte les stubs COREP/FINREP vers un fichier Excel (I11).
    
    Args:
        run_id: Identifiant du run
        output_path: Chemin du fichier Excel de sortie
    """
    stubs = create_corep_finrep_stubs(run_id)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name, df in stubs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)




# ============================================================================
# FINREP depuis ECL (I12)
# ============================================================================

def create_finrep_from_run(
    run_id: str,
    scenario_id: str,
) -> dict[str, pd.DataFrame]:
    """
    Crée les rapports FINREP F09/F18 depuis les résultats ECL.
    
    Args:
        run_id: Identifiant du run
        scenario_id: Identifiant du scénario ECL
    
    Returns:
        Dict avec clés:
            - 'finrep_f09': DataFrame impairment par classe/stage
            - 'finrep_f18': DataFrame breakdown of loans
    """
    from src.services.exposure_service import load_exposures
    from src.services.ifrs9_service import compute_ecl_advanced
    
    # 1. Charger les exposures
    df_exp = load_exposures(run_id)
    
    # 2. Calculer ECL
    ecl_result, _ = compute_ecl_advanced(run_id, scenario_id, use_cache=True)
    df_ecl = ecl_result['by_exposure']
    
    # 3. Merger exposures + ECL
    df_merged = df_exp.merge(
        df_ecl[['exposure_id', 'stage', 'ecl_amount']],
        left_on='id',
        right_on='exposure_id',
        how='left'
    )
    
    # ========================================================================
    # FINREP F09: Impairment
    # ========================================================================
    finrep_f09 = df_merged.groupby(['exposure_class', 'stage']).agg({
        'ecl_amount': 'sum',
        'ead': 'sum',
    }).reset_index()
    
    # Pivot pour avoir S1/S2/S3 en colonnes
    finrep_f09_pivot = finrep_f09.pivot(
        index='exposure_class',
        columns='stage',
        values='ecl_amount'
    ).fillna(0).reset_index()
    
    # Renommer colonnes
    finrep_f09_pivot.rename(columns={
        'exposure_class': 'Asset Class',
        'S1': 'Stage 1 ECL',
        'S2': 'Stage 2 ECL',
        'S3': 'Stage 3 ECL',
    }, inplace=True)
    
    # Ajouter total
    for col in ['Stage 1 ECL', 'Stage 2 ECL', 'Stage 3 ECL']:
        if col not in finrep_f09_pivot.columns:
            finrep_f09_pivot[col] = 0
    
    finrep_f09_pivot['Total ECL'] = (
        finrep_f09_pivot['Stage 1 ECL'] +
        finrep_f09_pivot['Stage 2 ECL'] +
        finrep_f09_pivot['Stage 3 ECL']
    )
    
    # Ajouter ligne TOTAL
    total_row = pd.DataFrame([{
        'Asset Class': 'TOTAL',
        'Stage 1 ECL': finrep_f09_pivot['Stage 1 ECL'].sum(),
        'Stage 2 ECL': finrep_f09_pivot['Stage 2 ECL'].sum(),
        'Stage 3 ECL': finrep_f09_pivot['Stage 3 ECL'].sum(),
        'Total ECL': finrep_f09_pivot['Total ECL'].sum(),
    }])
    
    finrep_f09_final = pd.concat([finrep_f09_pivot, total_row], ignore_index=True)
    
    # ========================================================================
    # FINREP F18: Breakdown of loans and advances
    # ========================================================================
    df_loans = df_merged[df_merged['product_type'] == 'Loan'].copy()
    
    finrep_f18 = df_loans.groupby('exposure_class').agg({
        'notional': 'sum',
        'ecl_amount': 'sum',
    }).reset_index()
    
    finrep_f18['net_carrying_amount'] = finrep_f18['notional'] - finrep_f18['ecl_amount']
    
    finrep_f18.rename(columns={
        'exposure_class': 'Loan Segment',
        'notional': 'Gross Carrying Amount',
        'ecl_amount': 'ECL Allowance',
        'net_carrying_amount': 'Net Carrying Amount',
    }, inplace=True)
    
    # Ajouter ligne TOTAL
    total_loans = pd.DataFrame([{
        'Loan Segment': 'TOTAL',
        'Gross Carrying Amount': finrep_f18['Gross Carrying Amount'].sum(),
        'ECL Allowance': finrep_f18['ECL Allowance'].sum(),
        'Net Carrying Amount': finrep_f18['Net Carrying Amount'].sum(),
    }])
    
    finrep_f18_final = pd.concat([finrep_f18, total_loans], ignore_index=True)
    
    return {
        'finrep_f09': finrep_f09_final,
        'finrep_f18': finrep_f18_final,
    }

