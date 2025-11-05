"""
Consolidation IFRS (IFRS 10/11) - Logique métier pure.

Ce module implémente la consolidation des états financiers selon IFRS 10/11 :
- Intégration globale (IG) : contrôle > 50%
- Intégration proportionnelle (IP) : contrôle conjoint 20-50%
- Mise en équivalence (ME) : influence notable < 20%
- Éliminations intra-groupe
- Intérêts minoritaires
- Conversion devises
"""


import pandas as pd


def build_group_structure(entities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Construit la structure de groupe à partir des entités.

    Args:
        entities_df: DataFrame avec colonnes minimales:
            - entity_id: str
            - parent_id: str (None pour la société mère)
            - ownership_pct: float (0-100)
            - method: str (IG, IP, ME)
            - currency: str

    Returns:
        DataFrame enrichi avec colonnes supplémentaires:
            - level: int (niveau hiérarchique, 0 pour la mère)
            - path: str (chemin depuis la mère)
            - is_consolidated: bool
    """
    df = entities_df.copy()

    # Optimisation dtypes
    df['entity_id'] = df['entity_id'].astype('category')
    if 'parent_id' in df.columns:
        df['parent_id'] = df['parent_id'].astype('category')
    df['method'] = df['method'].astype('category')
    df['currency'] = df['currency'].astype('category')
    df['ownership_pct'] = df['ownership_pct'].astype('float32')

    # Identifier la société mère (parent_id is None ou NaN)
    df['level'] = 0
    df['path'] = df['entity_id'].astype(str)
    df['is_consolidated'] = df['method'].isin(['IG', 'IP'])

    # Calculer les niveaux hiérarchiques (algorithme simple)
    # Note: Pour une implémentation complète, utiliser un algorithme de parcours d'arbre
    if 'parent_id' in df.columns:
        parent_map = df.set_index('entity_id')['parent_id'].to_dict()

        for idx in df.index:
            entity_id = df.loc[idx, 'entity_id']
            level = 0
            path = [str(entity_id)]
            current = entity_id

            # Remonter jusqu'à la racine
            while current in parent_map and pd.notna(parent_map[current]):
                parent = parent_map[current]
                path.insert(0, str(parent))
                current = parent
                level += 1
                if level > 10:  # Protection contre les boucles
                    break

            df.loc[idx, 'level'] = level
            df.loc[idx, 'path'] = ' > '.join(path)

    return df


def consolidate_statements(
    entities_df: pd.DataFrame,
    trial_balance_df: pd.DataFrame,
    fx_rates_df: pd.DataFrame | None = None,
    target_currency: str = "EUR",
) -> pd.DataFrame:
    """
    Consolide les états financiers selon IFRS 10/11.

    Args:
        entities_df: Structure de groupe (voir build_group_structure)
        trial_balance_df: Balance générale avec colonnes:
            - entity_id: str
            - account: str
            - amount: float
            - currency: str
            - period: str
        fx_rates_df: Taux de change (optionnel) avec colonnes:
            - from_ccy: str
            - to_ccy: str
            - rate: float
            - period: str
        target_currency: Devise cible pour la consolidation

    Returns:
        DataFrame consolidé avec colonnes:
            - entity_id, account, amount, currency, period
            - level, method, is_eliminated, minority_share
    """
    # Enrichir la structure de groupe
    entities_enriched = build_group_structure(entities_df)

    # Joindre trial balance avec structure de groupe
    conso_df = trial_balance_df.merge(
        entities_enriched[['entity_id', 'level', 'method', 'ownership_pct', 'currency', 'is_consolidated']],
        on='entity_id',
        how='left',
        suffixes=('', '_entity')
    )

    # Conversion devises si nécessaire
    if fx_rates_df is not None and not fx_rates_df.empty:
        conso_df = _convert_currencies(conso_df, fx_rates_df, target_currency)
    else:
        # Pas de conversion, garder les montants en devise d'origine
        conso_df['amount_consolidated'] = conso_df['amount']

    # Appliquer les méthodes de consolidation
    conso_df['amount_consolidated'] = conso_df.apply(
        lambda row: _apply_consolidation_method(
            row['amount_consolidated'],
            row['method'],
            row['ownership_pct']
        ),
        axis=1
    ).astype('float32')

    # Calculer les intérêts minoritaires
    conso_df['minority_share'] = conso_df.apply(
        lambda row: _compute_minority_share(
            row['amount_consolidated'],
            row['method'],
            row['ownership_pct']
        ),
        axis=1
    ).astype('float32')

    # Marquer les éliminations (à faire dans perform_intercompany_eliminations)
    conso_df['is_eliminated'] = False

    # Optimisation dtypes
    conso_df['account'] = conso_df['account'].astype('category')
    conso_df['period'] = conso_df['period'].astype('category')

    return conso_df


def _convert_currencies(
    df: pd.DataFrame,
    fx_rates_df: pd.DataFrame,
    target_currency: str
) -> pd.DataFrame:
    """Convertit les montants vers la devise cible."""
    df = df.copy()

    # Créer un mapping des taux de change
    fx_map = fx_rates_df.set_index(['from_ccy', 'to_ccy', 'period'])['rate'].to_dict()

    # Appliquer la conversion
    def convert_amount(row):
        if row['currency'] == target_currency:
            return row['amount']

        # Chercher le taux de change
        key = (row['currency'], target_currency, row['period'])
        if key in fx_map:
            return row['amount'] * fx_map[key]

        # Pas de taux trouvé, garder le montant original
        return row['amount']

    df['amount_consolidated'] = df.apply(convert_amount, axis=1)
    return df


def _apply_consolidation_method(
    amount: float,
    method: str,
    ownership_pct: float
) -> float:
    """Applique la méthode de consolidation."""
    if method == 'IG':
        # Intégration globale : 100% des montants
        return amount
    elif method == 'IP':
        # Intégration proportionnelle : % de détention
        return amount * (ownership_pct / 100.0)
    elif method == 'ME':
        # Mise en équivalence : pas de consolidation ligne à ligne
        return 0.0
    else:
        return amount


def _compute_minority_share(
    amount: float,
    method: str,
    ownership_pct: float
) -> float:
    """Calcule la part des intérêts minoritaires."""
    if method == 'IG' and ownership_pct < 100.0:
        # Intérêts minoritaires = (100% - % détention) × montant
        return amount * ((100.0 - ownership_pct) / 100.0)
    else:
        return 0.0


def perform_intercompany_eliminations(conso_df: pd.DataFrame) -> pd.DataFrame:
    """
    Effectue les éliminations intra-groupe.

    Args:
        conso_df: DataFrame consolidé (sortie de consolidate_statements)

    Returns:
        DataFrame avec éliminations appliquées
    """
    df = conso_df.copy()

    # Identifier les comptes intra-groupe (heuristique simple)
    # Comptes typiques : 401xxx (fournisseurs), 411xxx (clients), 70xxx (ventes), 60xxx (achats)
    intercompany_prefixes = ['401', '411', '70', '60']

    # Marquer les lignes à éliminer (vérifier les 2 ou 3 premiers caractères)
    df['is_eliminated'] = df['account'].astype(str).apply(
        lambda x: any(x.startswith(prefix) for prefix in intercompany_prefixes)
    )

    # Pour les lignes éliminées, mettre le montant à 0
    df.loc[df['is_eliminated'], 'amount_consolidated'] = 0.0

    return df


def compute_minority_interest(conso_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les intérêts minoritaires agrégés.

    Args:
        conso_df: DataFrame consolidé

    Returns:
        DataFrame avec intérêts minoritaires agrégés par entité
    """
    # Agréger les intérêts minoritaires par entité
    minority_df = conso_df.groupby('entity_id', observed=True).agg({
        'minority_share': 'sum'
    }).reset_index()

    minority_df.columns = ['entity_id', 'total_minority_interest']

    return minority_df

