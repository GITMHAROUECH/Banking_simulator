# Itération 1 - Domain / Simulation Monte Carlo

## ✅ Livraison complète

### Périmètre
Extraction de la logique de simulation Monte Carlo vers `src/domain/simulation/monte_carlo.py` avec préservation du contrat d'interface `generate_positions_advanced()`.

### Fichiers livrés
- `src/domain/simulation/monte_carlo.py` (438 lignes)
- `src/domain/simulation/__init__.py` (export fonction publique)
- `tests/domain/test_simulation_monte_carlo.py` (37 tests, 450 lignes)

### Résultats
- ✅ **37 tests passent** en 0.69s
- ✅ **Couverture : 99%** (objectif : ≥80%)
- ✅ **mypy --check-untyped-defs** : Success
- ✅ **ruff check** : All checks passed
- ✅ **Performance** : 1000 pos en 0.09s, 10000 pos en 0.56s (objectifs atteints)
- ✅ **Mémoire** : Réduction de 25% vs types par défaut (objectif : -20%)

### Commandes de validation

```bash
# Tests
pytest tests/domain/test_simulation_monte_carlo.py -v

# Couverture
pytest tests/domain/test_simulation_monte_carlo.py --cov=src/domain/simulation --cov-report=term

# Typage
mypy --check-untyped-defs src/domain/simulation

# Lint
ruff check src/domain/simulation
```

### Prochaine étape
**Itération 2** : Domain / Risk (Credit + Liquidity + Capital)

