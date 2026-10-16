# Note de conception — BudgetPilot

## 1. Objectif

BudgetPilot est une petite application web de suivi de tâches à dimension financière. Une tâche peut représenter, par exemple, une facture à régler, une dépense à prévoir ou une démarche administrative. Le montant associé est une estimation et ne constitue pas une opération bancaire réelle.

## 2. Architecture

- **Flask** reçoit les requêtes HTTP, valide les champs et choisit les vues à afficher.
- **PostgreSQL** conserve les tâches.
- **Psycopg 3** assure la connexion à la base et l'exécution de requêtes paramétrées.
- **Jinja** génère le HTML à partir de gabarits.
- **CSS** gère l'interface adaptative.
- **Docker Compose** démarre l'application et la base de données comme services distincts.

## 3. Modèle de données

La table `tasks` contient un identifiant, un titre, une description facultative, un statut, une priorité, une catégorie, un montant estimé, une date d'échéance et une date de création. Des contraintes SQL limitent les statuts et priorités autorisés et empêchent les montants négatifs.

## 4. Parcours principaux

1. L'utilisateur soumet le formulaire d'ajout.
2. Flask vérifie le titre, le statut, la priorité, la catégorie et le montant.
3. Une requête SQL paramétrée enregistre les données.
4. La page d'accueil recharge les tâches et calcule les indicateurs.
5. L'utilisateur peut filtrer, modifier, changer le statut ou supprimer une tâche.

## 5. Choix de conception et limites

Les filtres sont traités côté serveur pour rester simples à comprendre. Les montants sont stockés en `NUMERIC` pour éviter les erreurs d'arrondi propres aux nombres flottants. L'application n'inclut pas de comptes utilisateurs, d'authentification, de synchronisation bancaire ni de gestion multi-utilisateur : elle est prévue pour un environnement pédagogique local.

## 6. Plan de tests manuel

| Cas | Résultat attendu |
|---|---|
| Ajouter une tâche avec un titre et un montant valide | La tâche apparaît dans la liste |
| Envoyer un titre vide | Un message d'erreur s'affiche |
| Saisir un montant négatif | La validation refuse la saisie |
| Changer le statut | Le statut est mis à jour |
| Filtrer par catégorie | Seules les tâches correspondantes apparaissent |
| Rechercher une chaîne absente | Un état vide est affiché |
| Supprimer une tâche | Elle disparaît de la liste |
| Appeler `/health` avec la base disponible | Réponse JSON avec statut `ok` |
| Appeler `/api/tasks` | Réponse JSON contenant la liste des tâches |

