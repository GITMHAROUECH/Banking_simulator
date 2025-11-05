# Journal d'Arbitrages Techniques - Itération 5

## 1. Services vs Domain : Où placer la validation ?

**Décision** : Validation des entrées au niveau Services.

**Justification** :
- **Services** : Validation des paramètres d'entrée (non vides, colonnes requises, types)
- **Domain** : Validation métier (bornes de valeurs, cohérence des données)
- **Avantages** : Messages d'erreur explicites, fail-fast, testabilité

**Implémentation** :
```python
def compute_rwa(positions_df: pd.DataFrame) -> pd.DataFrame:
    if positions_df.empty:
        raise ValueError("positions_df ne peut pas être vide")
    
    required_cols = ['position_id', 'exposure_class', 'ead']
    missing_cols = [col for col in required_cols if col not in positions_df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes: {missing_cols}")
    
    return domain_calculate_rwa(positions_df)
```

## 2. Export Excel : Bibliothèque openpyxl vs xlsxwriter

**Décision** : openpyxl via `pandas.ExcelWriter`.

**Justification** :
- **openpyxl** : Déjà installé, intégration native pandas
- **xlsxwriter** : Plus rapide mais nécessite installation supplémentaire
- **Simplicité** : Code plus court avec pandas.ExcelWriter

**Implémentation** :
```python
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    positions_df.to_excel(writer, sheet_name='Positions', index=False)
    rwa_df.to_excel(writer, sheet_name='RWA', index=False)
    # ...
```

## 3. Consolidation : Réconciliation simplifiée vs Réconciliation complète

**Décision** : Réconciliation simplifiée pour I5.

**Justification** :
- **I5** : Utilise trial_balance_df comme source "risk" (simplifié)
- **I6+** : Réconciliation complète avec risk_df séparé (via DB)
- **Pragmatisme** : Permet de tester l'orchestration sans dépendance DB

**Limitation connue** :
- La réconciliation I5 compare trial_balance avec lui-même (simplifié)
- En production, il faudra un risk_df distinct (sera implémenté en I6)

## 4. Adaptateurs : Wrapper vs Ré-export

**Décision** : Wrapper avec délégation explicite.

**Justification** :
- **Traçabilité** : Chaque adaptateur appelle explicitement un service
- **Flexibilité** : Permet d'ajouter de la logique si nécessaire
- **Clarté** : Code plus lisible qu'un simple ré-export

**Implémentation** :
```python
def generate_positions_advanced(num_positions: int, seed: int, config=None):
    return run_simulation(
        num_positions=num_positions,
        seed=seed,
        config=config,
        include_derivatives=False
    )
```

## 5. Typage strict : mypy --strict dès I5 vs I9

**Décision** : mypy --strict sur Services dès I5, Domain en I9.

**Justification** :
- **Services** : Code neuf, typage strict dès le début
- **Domain** : Code I1-I4 avec --check-untyped-defs, migration strict en I9
- **Pragmatisme** : Évite de bloquer I5 sur corrections Domain

**Note** :
- Les Services sont correctement typés (strict)
- Les erreurs mypy proviennent des dépendances Domain importées
- Correction complète en I9 (Qualité)

## Conclusion

Les arbitrages techniques de l'Itération 5 privilégient :
- **Validation** : Au niveau Services (fail-fast)
- **Simplicité** : openpyxl, réconciliation simplifiée
- **Compatibilité** : Adaptateurs avec wrappers explicites
- **Pragmatisme** : Typage strict progressif (Services I5, Domain I9)

**Prochaine étape** : Itération 6 (Persistence SQLite avec artifacts)

