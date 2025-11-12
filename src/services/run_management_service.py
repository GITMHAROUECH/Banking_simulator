"""
Service de gestion avancée des runs (I13).
Fonctionnalités: liste, détails, suppression, clonage, export/import, comparaison, validation.
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from db.base import get_session
from db.models import Exposure, RunComparison, RunLog, SimulationRun


def list_runs(
    status_filter: str | None = None,
    favorites_only: bool = False,
    tags_filter: list[str] | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """
    Liste les runs avec filtres et pagination.
    
    Args:
        status_filter: Filtrer par statut (completed, pending, failed)
        favorites_only: Ne retourner que les favoris
        tags_filter: Filtrer par tags
        date_from: Date de début
        date_to: Date de fin
        limit: Nombre de résultats par page
        offset: Offset pour pagination
        
    Returns:
        Tuple (liste des runs, total count)
    """
    session: Session = get_session()

    query = session.query(SimulationRun)

    # Filtres
    if status_filter:
        query = query.filter(SimulationRun.status == status_filter)

    if favorites_only:
        query = query.filter(SimulationRun.is_favorite == True)

    if tags_filter:
        # Tags stockés en JSON, filtrer si au moins un tag matche
        for tag in tags_filter:
            query = query.filter(SimulationRun.tags.like(f'%{tag}%'))

    if date_from:
        query = query.filter(SimulationRun.run_date >= date_from)

    if date_to:
        query = query.filter(SimulationRun.run_date <= date_to)

    # Count total
    total_count = query.count()

    # Pagination et tri
    runs = query.order_by(desc(SimulationRun.run_date)).limit(limit).offset(offset).all()

    # Convertir en dict
    runs_list = []
    for run in runs:
        tags = json.loads(run.tags) if run.tags else []
        runs_list.append({
            'run_id': run.run_id,
            'run_date': run.run_date,
            'status': run.status,
            'total_exposures': run.total_exposures,
            'total_notional': float(run.total_notional) if run.total_notional else None,
            'duration_seconds': float(run.duration_seconds) if run.duration_seconds else None,
            'is_favorite': run.is_favorite,
            'tags': tags,
            'parent_run_id': run.parent_run_id,
            'checksum': run.checksum,
        })

    return runs_list, total_count


def get_run_details(run_id: str) -> dict[str, Any] | None:
    """
    Récupère les détails complets d'un run.
    
    Args:
        run_id: Identifiant du run
        
    Returns:
        Dictionnaire avec métadonnées, stats, logs
    """
    session: Session = get_session()

    run = session.query(SimulationRun).filter_by(run_id=run_id).first()
    if not run:
        return None

    # Stats des exposures
    exposure_stats = session.query(
        Exposure.product_type,
        func.count(Exposure.id).label('count'),
        func.sum(Exposure.ead).label('total_ead'),
        func.sum(Exposure.notional).label('total_notional'),
    ).filter_by(run_id=run_id).group_by(Exposure.product_type).all()

    stats_by_product = []
    for stat in exposure_stats:
        stats_by_product.append({
            'product_type': stat.product_type,
            'count': stat.count,
            'total_ead': float(stat.total_ead) if stat.total_ead else 0,
            'total_notional': float(stat.total_notional) if stat.total_notional else 0,
        })

    # Logs récents
    logs = session.query(RunLog).filter_by(run_id=run_id).order_by(desc(RunLog.timestamp)).limit(50).all()
    logs_list = []
    for log in logs:
        logs_list.append({
            'timestamp': log.timestamp,
            'level': log.level,
            'message': log.message,
        })

    # Config
    config = json.loads(run.config_json) if run.config_json else {}
    tags = json.loads(run.tags) if run.tags else []

    return {
        'run_id': run.run_id,
        'run_date': run.run_date,
        'status': run.status,
        'total_exposures': run.total_exposures,
        'total_notional': float(run.total_notional) if run.total_notional else None,
        'duration_seconds': float(run.duration_seconds) if run.duration_seconds else None,
        'checksum': run.checksum,
        'is_favorite': run.is_favorite,
        'tags': tags,
        'parent_run_id': run.parent_run_id,
        'notes': run.notes,
        'config': config,
        'stats_by_product': stats_by_product,
        'logs': logs_list,
    }


def delete_run(run_id: str) -> bool:
    """
    Supprime un run et toutes ses données associées.
    
    Args:
        run_id: Identifiant du run
        
    Returns:
        True si suppression réussie
    """
    session: Session = get_session()

    try:
        # Supprimer les exposures
        session.query(Exposure).filter_by(run_id=run_id).delete()

        # Supprimer les logs
        session.query(RunLog).filter_by(run_id=run_id).delete()

        # Supprimer le run
        session.query(SimulationRun).filter_by(run_id=run_id).delete()

        session.commit()
        return True

    except Exception as e:
        session.rollback()
        raise e


def toggle_favorite(run_id: str) -> bool:
    """
    Bascule le statut favori d'un run.
    
    Args:
        run_id: Identifiant du run
        
    Returns:
        Nouveau statut favori
    """
    session: Session = get_session()

    run = session.query(SimulationRun).filter_by(run_id=run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found")

    run.is_favorite = not run.is_favorite
    session.commit()

    return run.is_favorite


def update_tags(run_id: str, tags: list[str]) -> None:
    """
    Met à jour les tags d'un run.
    
    Args:
        run_id: Identifiant du run
        tags: Liste des tags
    """
    session: Session = get_session()

    run = session.query(SimulationRun).filter_by(run_id=run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found")

    run.tags = json.dumps(tags)
    session.commit()


def update_notes(run_id: str, notes: str) -> None:
    """
    Met à jour les notes d'un run.
    
    Args:
        run_id: Identifiant du run
        notes: Texte des notes
    """
    session: Session = get_session()

    run = session.query(SimulationRun).filter_by(run_id=run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found")

    run.notes = notes
    session.commit()


def clone_run(
    source_run_id: str,
    modifications: dict[str, Any] | None = None,
) -> str:
    """
    Clone un run existant avec modifications optionnelles.
    
    Args:
        source_run_id: Run source à cloner
        modifications: Modifications à appliquer (seed, num_exposures, etc.)
        
    Returns:
        ID du nouveau run créé
    """
    session: Session = get_session()

    # Récupérer le run source
    source_run = session.query(SimulationRun).filter_by(run_id=source_run_id).first()
    if not source_run:
        raise ValueError(f"Source run {source_run_id} not found")

    # Config source
    config = json.loads(source_run.config_json) if source_run.config_json else {}

    # Appliquer modifications
    if modifications:
        config.update(modifications)

    # Générer nouveau run_id
    new_run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    # Créer nouveau run
    new_run = SimulationRun(
        run_id=new_run_id,
        params_hash=hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        run_date=datetime.utcnow(),
        status='pending',
        config_json=json.dumps(config),
        parent_run_id=source_run_id,
        tags=source_run.tags,
    )

    session.add(new_run)
    session.commit()

    # Log
    log = RunLog(
        id=str(uuid.uuid4()),
        run_id=new_run_id,
        timestamp=datetime.utcnow(),
        level='INFO',
        message=f'Run cloned from {source_run_id}',
    )
    session.add(log)
    session.commit()

    return new_run_id


def compute_checksum(run_id: str) -> str:
    """
    Calcule le checksum SHA256 des exposures d'un run.
    
    Args:
        run_id: Identifiant du run
        
    Returns:
        Checksum SHA256
    """
    session: Session = get_session()

    # Récupérer toutes les exposures
    exposures = session.query(Exposure).filter_by(run_id=run_id).order_by(Exposure.id).all()

    # Construire une chaîne représentative
    data_str = ""
    for exp in exposures:
        data_str += f"{exp.id}|{exp.product_type}|{exp.ead}|{exp.pd}|{exp.lgd}|"

    # Calculer SHA256
    checksum = hashlib.sha256(data_str.encode()).hexdigest()

    # Mettre à jour le run
    run = session.query(SimulationRun).filter_by(run_id=run_id).first()
    if run:
        run.checksum = checksum
        session.commit()

    return checksum


def validate_run(run_id: str) -> dict[str, Any]:
    """
    Valide l'intégrité d'un run.
    
    Args:
        run_id: Identifiant du run
        
    Returns:
        Dictionnaire avec résultats de validation
    """
    session: Session = get_session()

    run = session.query(SimulationRun).filter_by(run_id=run_id).first()
    if not run:
        return {'valid': False, 'error': 'Run not found'}

    # Vérifier nombre d'exposures
    actual_count = session.query(func.count(Exposure.id)).filter_by(run_id=run_id).scalar()
    expected_count = run.total_exposures

    count_valid = actual_count == expected_count if expected_count else True

    # Vérifier checksum
    current_checksum = compute_checksum(run_id)
    checksum_valid = current_checksum == run.checksum if run.checksum else True

    # Vérifier données nulles
    null_ead_count = session.query(func.count(Exposure.id)).filter(
        and_(Exposure.run_id == run_id, Exposure.ead == None)
    ).scalar()

    null_pd_count = session.query(func.count(Exposure.id)).filter(
        and_(Exposure.run_id == run_id, Exposure.pd == None)
    ).scalar()

    return {
        'valid': count_valid and checksum_valid and null_ead_count == 0,
        'run_id': run_id,
        'count_valid': count_valid,
        'expected_count': expected_count,
        'actual_count': actual_count,
        'checksum_valid': checksum_valid,
        'expected_checksum': run.checksum,
        'actual_checksum': current_checksum,
        'null_ead_count': null_ead_count,
        'null_pd_count': null_pd_count,
    }





def compare_runs(run_ids: list[str]) -> dict[str, Any]:
    """
    Compare plusieurs runs et retourne les métriques comparatives.
    
    Args:
        run_ids: Liste des run_ids à comparer (2-4 runs)
        
    Returns:
        Dictionnaire avec comparaisons
    """
    if len(run_ids) < 2 or len(run_ids) > 4:
        raise ValueError("Can only compare 2-4 runs")

    session: Session = get_session()

    comparison = {
        'run_ids': run_ids,
        'runs_metadata': [],
        'metrics_comparison': {},
        'exposures_comparison': {},
    }

    # Récupérer métadonnées de chaque run
    for run_id in run_ids:
        run = session.query(SimulationRun).filter_by(run_id=run_id).first()
        if not run:
            continue

        # Stats exposures
        total_ead = session.query(func.sum(Exposure.ead)).filter_by(run_id=run_id).scalar() or 0
        avg_pd = session.query(func.avg(Exposure.pd)).filter_by(run_id=run_id).scalar() or 0
        avg_lgd = session.query(func.avg(Exposure.lgd)).filter_by(run_id=run_id).scalar() or 0

        comparison['runs_metadata'].append({
            'run_id': run_id,
            'run_date': run.run_date,
            'status': run.status,
            'total_exposures': run.total_exposures,
            'total_notional': float(run.total_notional) if run.total_notional else 0,
            'total_ead': float(total_ead),
            'avg_pd': float(avg_pd),
            'avg_lgd': float(avg_lgd),
        })

    # Comparaison par produit
    for run_id in run_ids:
        product_stats = session.query(
            Exposure.product_type,
            func.count(Exposure.id).label('count'),
            func.sum(Exposure.ead).label('total_ead'),
        ).filter_by(run_id=run_id).group_by(Exposure.product_type).all()

        comparison['exposures_comparison'][run_id] = {}
        for stat in product_stats:
            comparison['exposures_comparison'][run_id][stat.product_type] = {
                'count': stat.count,
                'total_ead': float(stat.total_ead) if stat.total_ead else 0,
            }

    return comparison


def save_comparison(name: str, run_ids: list[str], notes: str | None = None) -> str:
    """
    Sauvegarde une comparaison pour référence future.
    
    Args:
        name: Nom de la comparaison
        run_ids: Liste des run_ids comparés
        notes: Notes optionnelles
        
    Returns:
        ID de la comparaison
    """
    session: Session = get_session()

    comparison_id = str(uuid.uuid4())

    comparison = RunComparison(
        id=comparison_id,
        name=name,
        run_ids=json.dumps(run_ids),
        created_at=datetime.utcnow(),
        notes=notes,
    )

    session.add(comparison)
    session.commit()

    return comparison_id


def list_comparisons() -> list[dict[str, Any]]:
    """
    Liste toutes les comparaisons sauvegardées.
    
    Returns:
        Liste des comparaisons
    """
    session: Session = get_session()

    comparisons = session.query(RunComparison).order_by(desc(RunComparison.created_at)).all()

    result = []
    for comp in comparisons:
        result.append({
            'id': comp.id,
            'name': comp.name,
            'run_ids': json.loads(comp.run_ids),
            'created_at': comp.created_at,
            'notes': comp.notes,
        })

    return result


def export_run(run_id: str, format: str = 'json') -> tuple[bytes, str]:
    """
    Exporte un run complet.
    
    Args:
        run_id: Identifiant du run
        format: Format d'export (json, parquet)
        
    Returns:
        Tuple (données binaires, nom de fichier)
    """
    session: Session = get_session()

    # Récupérer métadonnées
    run = session.query(SimulationRun).filter_by(run_id=run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found")

    # Récupérer exposures
    exposures = session.query(Exposure).filter_by(run_id=run_id).all()

    if format == 'json':
        # Export JSON
        data = {
            'metadata': {
                'run_id': run.run_id,
                'run_date': run.run_date.isoformat(),
                'status': run.status,
                'total_exposures': run.total_exposures,
                'total_notional': float(run.total_notional) if run.total_notional else None,
                'config': json.loads(run.config_json) if run.config_json else {},
                'checksum': run.checksum,
            },
            'exposures': []
        }

        for exp in exposures:
            data['exposures'].append({
                'id': exp.id,
                'product_type': exp.product_type,
                'counterparty_id': exp.counterparty_id,
                'currency': exp.currency,
                'notional': float(exp.notional) if exp.notional else None,
                'ead': float(exp.ead) if exp.ead else None,
                'pd': float(exp.pd) if exp.pd else None,
                'lgd': float(exp.lgd) if exp.lgd else None,
                'entity': exp.entity,
            })

        json_bytes = json.dumps(data, indent=2).encode('utf-8')
        filename = f"{run_id}_export.json"
        return json_bytes, filename

    elif format == 'parquet':
        # Export Parquet (exposures seulement)
        df = pd.read_sql(
            session.query(Exposure).filter_by(run_id=run_id).statement,
            session.bind
        )

        parquet_bytes = df.to_parquet(index=False)
        filename = f"{run_id}_exposures.parquet"
        return parquet_bytes, filename

    else:
        raise ValueError(f"Unsupported format: {format}")


def import_run(file_path: str) -> str:
    """
    Importe un run depuis un fichier JSON.
    
    Args:
        file_path: Chemin du fichier JSON
        
    Returns:
        ID du run importé
    """
    session: Session = get_session()

    # Lire le fichier
    with open(file_path) as f:
        data = json.load(f)

    metadata = data['metadata']
    exposures_data = data['exposures']

    # Créer nouveau run
    new_run_id = f"run_imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    new_run = SimulationRun(
        run_id=new_run_id,
        params_hash=hashlib.sha256(json.dumps(metadata['config'], sort_keys=True).encode()).hexdigest(),
        run_date=datetime.utcnow(),
        status='completed',
        total_exposures=metadata['total_exposures'],
        total_notional=metadata['total_notional'],
        config_json=json.dumps(metadata['config']),
        checksum=metadata.get('checksum'),
    )

    session.add(new_run)
    session.commit()

    # Créer exposures
    for exp_data in exposures_data:
        exposure = Exposure(
            id=str(uuid.uuid4()),
            run_id=new_run_id,
            product_type=exp_data['product_type'],
            counterparty_id=exp_data.get('counterparty_id'),
            currency=exp_data['currency'],
            notional=exp_data.get('notional'),
            ead=exp_data.get('ead'),
            pd=exp_data.get('pd'),
            lgd=exp_data.get('lgd'),
            entity=exp_data['entity'],
        )
        session.add(exposure)

    session.commit()

    # Log
    log = RunLog(
        id=str(uuid.uuid4()),
        run_id=new_run_id,
        timestamp=datetime.utcnow(),
        level='INFO',
        message=f'Run imported from {file_path}',
    )
    session.add(log)
    session.commit()

    return new_run_id


def cleanup_old_runs(days_threshold: int = 30, dry_run: bool = True) -> dict[str, Any]:
    """
    Nettoie les runs anciens non favoris.
    
    Args:
        days_threshold: Nombre de jours avant suppression
        dry_run: Si True, ne supprime pas réellement
        
    Returns:
        Statistiques de nettoyage
    """
    session: Session = get_session()

    cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

    # Trouver les runs à supprimer
    runs_to_delete = session.query(SimulationRun).filter(
        and_(
            SimulationRun.run_date < cutoff_date,
            SimulationRun.is_favorite == False,
        )
    ).all()

    stats = {
        'dry_run': dry_run,
        'cutoff_date': cutoff_date,
        'runs_found': len(runs_to_delete),
        'runs_deleted': 0,
        'exposures_deleted': 0,
        'run_ids': [run.run_id for run in runs_to_delete],
    }

    if not dry_run:
        for run in runs_to_delete:
            # Compter exposures
            exp_count = session.query(func.count(Exposure.id)).filter_by(run_id=run.run_id).scalar()
            stats['exposures_deleted'] += exp_count

            # Supprimer
            delete_run(run.run_id)
            stats['runs_deleted'] += 1

    return stats


def add_log(run_id: str, level: str, message: str) -> None:
    """
    Ajoute un log pour un run.
    
    Args:
        run_id: Identifiant du run
        level: Niveau (INFO, WARNING, ERROR)
        message: Message du log
    """
    session: Session = get_session()

    log = RunLog(
        id=str(uuid.uuid4()),
        run_id=run_id,
        timestamp=datetime.utcnow(),
        level=level,
        message=message,
    )

    session.add(log)
    session.commit()

