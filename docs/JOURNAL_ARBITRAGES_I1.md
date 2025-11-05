# Journal d'Arbitrages Techniques - Itération 1

## Décisions prises lors de la refactorisation Domain / Simulation

### 1. Optimisation des dtypes pour réduction mémoire (-25%)

**Décision** : Utiliser `category` pour les colonnes catégorielles et `float32` pour les colonnes numériques.

**Justification** :
- Les colonnes `entity_id`, `product_id`, `exposure_class`, `currency` ont un nombre limité de valeurs uniques (3-12 valeurs)
- `category` réduit la mémoire de ~80% pour ces colonnes vs `object`
- `float32` au lieu de `float64` réduit la mémoire de 50% pour les colonnes numériques
- `int8` au lieu de `int64` pour `stage` (valeurs 1-3 uniquement)

**Résultat** : Réduction mémoire de 25% vs types par défaut (objectif : -20%)

---

### 2. Vectorisation partielle vs boucle Python

**Décision** : Conserver une boucle Python pour générer les positions individuellement.

**Justification** :
- Logique complexe avec conditions imbriquées (facilities vs prêts standards)
- CCF variable selon le type de produit
- Vectorisation complète aurait nécessité des masques multiples et du code moins lisible
- Performance actuelle : 10,000 positions en 0.56s (objectif : <60s) → largement suffisant

**Alternative non retenue** : Vectorisation NumPy complète (complexité élevée, gain marginal)

---

### 3. Gestion des catégories de produits

**Décision** : Utiliser des listes de constantes (`DEFAULT_ENTITIES`, `DEFAULT_PRODUCTS`, etc.) au lieu de Enums.

**Justification** :
- Simplicité : pas besoin d'importer des Enums dans les tests
- Flexibilité : facile d'ajouter de nouveaux produits sans modifier le code
- Compatibilité : les listes sont directement utilisables dans `random.choice()` et `index % len(list)`

**Alternative non retenue** : Enums (plus verbeux, pas de gain fonctionnel)

---

### 4. Reproductibilité via seed

**Décision** : Initialiser à la fois `random.seed()` et `np.random.seed()` dans le constructeur.

**Justification** :
- Le code utilise à la fois `random` (Python stdlib) et `numpy.random`
- Les deux doivent être initialisés pour garantir la reproductibilité complète
- Tests de reproductibilité passent avec hash MD5 identique

**Validation** : Test `test_seed_reproducible()` vérifie que seed identique → résultats identiques

---

### 5. Type hints avec `# type: ignore` pour mypy

**Décision** : Ajouter `# type: ignore[assignment]` sur 3 lignes où mypy détecte des conflits int/float.

**Justification** :
- `random.randint()` retourne un `int` mais on le convertit immédiatement en `float`
- Mypy en mode `--check-untyped-defs` est strict sur ces conversions
- Les `# type: ignore` sont documentés et seront corrigés lors du passage à `--strict` (Itération 9)
- Fonctionnellement correct : les tests passent et les valeurs sont correctes

**Alternative non retenue** : Refactoriser pour éviter les conversions (complexité inutile pour I1)

---

## Métriques finales

| Métrique | Objectif | Résultat | Statut |
|----------|----------|----------|--------|
| Couverture tests | ≥80% | 99% | ✅ |
| Performance 1000 pos | ≤10s | 0.09s | ✅ |
| Performance 10000 pos | ≤60s | 0.56s | ✅ |
| Réduction mémoire | -20% | -25% | ✅ |
| mypy --check-untyped-defs | Success | Success | ✅ |
| ruff check | Pass | Pass | ✅ |
| Tests passants | 100% | 37/37 | ✅ |

---

## Points d'attention pour les itérations suivantes

1. **Type hints stricts** : Passer à `mypy --strict` en Itération 9 et corriger les `# type: ignore`
2. **Vectorisation** : Si performance devient un problème (>100k positions), envisager vectorisation NumPy
3. **Config externe** : Actuellement config en Dict Python, migrer vers YAML/JSON en Itération 5 (Services)
4. **Dérivés** : Support `include_derivatives=True` sera ajouté en Itération 4 (Domain / Consolidation)

