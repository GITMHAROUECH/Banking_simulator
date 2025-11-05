# Journal d'Arbitrages Techniques - Itération 4

## 1. Consolidation : Algorithme hiérarchique vs Parcours d'arbre complet

**Décision** : Algorithme simple de remontée vers la racine.

**Justification** :
- Simplicité : Code facile à comprendre et maintenir
- Performance suffisante : O(n×h) où h = hauteur de l'arbre (typiquement < 5)
- Protection contre les boucles : Limite à 10 niveaux

**Alternative envisagée** :
- Parcours d'arbre complet avec topological sort : plus robuste mais plus complexe

## 2. Éliminations intra-groupe : Règles heuristiques vs Mapping explicite

**Décision** : Heuristique basée sur les préfixes de comptes (401, 411, 70, 60).

**Justification** :
- Simplicité : Pas besoin de mapping externe
- Couverture : Capture la majorité des cas typiques
- Extensibilité : Facile d'ajouter des préfixes

**Implémentation** :
```python
intercompany_prefixes = ['401', '411', '70', '60']
df['is_eliminated'] = df['account'].astype(str).apply(
    lambda x: any(x.startswith(prefix) for prefix in intercompany_prefixes)
)
```

**Alternative envisagée** :
- Mapping explicite compte → flag intra-groupe : plus précis mais nécessite configuration

## 3. Conversion devises : Taux spot vs Taux moyens

**Décision** : Taux spot fournis dans fx_rates_df.

**Justification** :
- Flexibilité : L'appelant peut fournir des taux spot ou moyens
- Simplicité : Pas de calcul de moyenne dans le module
- Conformité : Selon IFRS, les taux à utiliser dépendent du contexte

**Implémentation** :
- Si fx_rates_df fourni : conversion avec lookup dans le dict
- Sinon : montants en devise d'origine

## 4. Réconciliation : Agrégation par entité vs Agrégation détaillée

**Décision** : Agrégation par entité + période.

**Justification** :
- Simplicité : Moins de lignes à réconcilier
- Performance : Calculs plus rapides
- Lisibilité : Résultats plus faciles à interpréter

**Implémentation** :
```python
ledger_agg = ledger_df.groupby(['entity_id', 'period']).agg({'amount': 'sum'})
risk_agg = risk_df.groupby(['entity_id', 'period']).agg({'amount': 'sum'})
```

**Alternative envisagée** :
- Réconciliation ligne à ligne avec mapping compte ↔ risk_bucket : plus précis mais complexe

## 5. Root cause hints : Heuristique vs Machine Learning

**Décision** : Heuristique simple basée sur les seuils d'écart.

**Justification** :
- Simplicité : Pas de dépendance ML
- Interprétabilité : Règles claires et explicables
- Performance : Calcul instantané

**Règles** :
- delta_pct < 5% → "Rounding differences"
- delta_pct < 10% → "Timing differences or mapping issues"
- delta_pct < 20% → "Scope differences (perimeter mismatch)"
- delta_pct >= 20% → "Significant variance - manual investigation required"

**Alternative envisagée** :
- ML classifier entraîné sur historique : plus précis mais nécessite données d'entraînement

## Conclusion

Les arbitrages techniques de l'Itération 4 privilégient :
- **Simplicité** : Algorithmes simples et maintenables
- **Heuristiques** : Règles basées sur l'expérience métier
- **Flexibilité** : Support de multiples formats d'entrée
- **Performance** : Optimisations ciblées (dtypes, vectorisation)

**Prochaine étape** : Itération 5 (Services d'orchestration)

