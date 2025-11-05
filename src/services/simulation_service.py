"""
Service d'orchestration pour la simulation Monte Carlo.

Ce service coordonne la génération de positions bancaires,
avec option d'inclure les produits dérivés.
"""
import warnings

import pandas as pd

from src.domain.simulation import (
    generate_positions_advanced as domain_generate_positions,
)
from src.services.persistence_service import (
    compute_params_hash,
    load_dataframe,
    save_dataframe,
)


def run_simulation(
    num_positions: int,
    seed: int,
    config: dict[str, object] | None = None,
    include_derivatives: bool = False,
    use_cache: bool = True
) -> tuple[pd.DataFrame, bool]:
    """
    Lance une simulation Monte Carlo de positions bancaires.

    Args:
        num_positions: Nombre de positions à générer
        seed: Graine aléatoire pour reproductibilité
        config: Configuration optionnelle (dict)
        include_derivatives: Si True, inclut les produits dérivés
        use_cache: Si True, utilise le cache params_hash (défaut: True)

    Returns:
        Tuple (DataFrame, cache_hit):
            - DataFrame avec colonnes minimales:
                position_id, entity_id, product_id, exposure_class,
                currency, ead, pd, lgd, maturity, stage, ecl_provision
            - cache_hit: True si chargé depuis le cache, False si calculé

    Raises:
        ValueError: Si num_positions <= 0 ou seed < 0
    """
    # Validation des paramètres
    if num_positions <= 0:
        raise ValueError(f"num_positions doit être > 0, reçu: {num_positions}")
    if seed < 0:
        raise ValueError(f"seed doit être >= 0, reçu: {seed}")

    # Calculer le hash des paramètres pour le cache (I6)
    params = {
        "num_positions": num_positions,
        "seed": seed,
        "config": config or {},
        "include_derivatives": include_derivatives,
    }
    params_hash = compute_params_hash(params)

    # Tenter de charger depuis le cache (I6)
    if use_cache:
        cached_df = load_dataframe("positions", params_hash)
        if cached_df is not None:
            return (cached_df, True)  # Cache hit

    # Générer les positions via le domain
    positions_df = domain_generate_positions(
        num_positions=num_positions,
        seed=seed,
        config=config
    )

    # TODO: Ajouter les dérivés si include_derivatives=True
    if include_derivatives:
        warnings.warn(
            "include_derivatives=True non implémenté, ignoré",
            UserWarning,
            stacklevel=2
        )

    # Sauvegarder dans le cache (I6)
    if use_cache:
        save_dataframe("positions", params_hash, positions_df)

    return (positions_df, False)  # Cache miss

