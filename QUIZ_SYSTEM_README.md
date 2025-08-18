# Système de Quiz Dynamique - CV Analyzer Pro

## Vue d'ensemble

Le système de quiz dynamique permet aux recruteurs d'assigner des quiz personnalisés aux candidats basés sur les compétences requises du poste. Contrairement au système précédent qui générait des quiz basés sur les compétences du candidat, ce nouveau système génère des quiz basés sur les compétences requises du poste créé par le recruteur.

## Fonctionnalités

### Pour les Recruteurs (HR)

1. **Bouton "Évaluer Quiz"** dans la liste des candidats
   - Ajouté dans la page "Détails du Poste"
   - Permet d'assigner un quiz à un candidat spécifique
   - Le quiz est généré dynamiquement basé sur les compétences requises du poste

2. **Génération de Quiz Dynamique**
   - Utilise les compétences requises définies dans le poste
   - Génère des questions pertinentes pour évaluer les compétences nécessaires
   - Évite la répétition de questions précédentes

3. **Suivi des Assignations**
   - API pour récupérer les assignations de quiz par poste
   - Statut des quiz (assigné, en cours, complété)

### Pour les Candidats

1. **Bouton "Passer Quiz"** près de la cloche de notification
   - Affiché dans l'en-tête quand des quiz sont assignés
   - Compteur de quiz non complétés
   - Dropdown avec la liste des quiz assignés

2. **Interface de Quiz Interactive**
   - Page dédiée pour passer les quiz
   - Navigation entre les questions
   - Barre de progression
   - Soumission et calcul automatique des résultats

## Structure de la Base de Données

### Nouvelle Table: `job_quiz_assignments`

```sql
CREATE TABLE job_quiz_assignments (
    id INTEGER PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    candidate_id INTEGER REFERENCES profile_candidat(id),
    assigned_by INTEGER REFERENCES hr_admins(id),
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME,
    status VARCHAR(50) DEFAULT 'assigned',
    quiz_attempt_id INTEGER REFERENCES quiz_attempts(id),
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### HR Endpoints

- `POST /api/assign-quiz/{job_id}/{candidate_id}` - Assigner un quiz
- `GET /api/job-quiz-assignments/{job_id}` - Récupérer les assignations d'un poste
- `POST /api/generate-job-quiz/{job_id}/{candidate_id}` - Générer un quiz

### Candidate Endpoints

- `GET /api/my-assigned-quizzes` - Récupérer les quiz assignés
- `GET /api/take-quiz/{assignment_id}` - Prendre un quiz assigné
- `POST /api/submit-quiz/{assignment_id}` - Soumettre les réponses
- `GET /api/quizzes/count` - Compter les quiz non complétés
- `GET /api/quizzes/recent` - Récupérer les quiz récents

## Pages et Templates

### Nouveaux Templates

1. **`templates/client-dep/take-quiz.html`**
   - Interface pour passer les quiz
   - Navigation interactive
   - Design moderne et responsive

### Modifications Existantes

1. **`templates/HR-dep/job-details.html`**
   - Ajout du bouton "Évaluer Quiz" pour chaque candidat

2. **`static/client-dep/components/header.html`**
   - Ajout du bouton quiz près de la cloche de notification
   - Dropdown pour afficher les quiz assignés

## Services

### QuizService

Nouvelles méthodes ajoutées :

- `generate_job_based_quiz()` - Génère un quiz basé sur les compétences du poste
- `assign_quiz_to_candidate()` - Assigne un quiz à un candidat
- `get_assigned_quizzes_for_candidate()` - Récupère les quiz assignés

## Utilisation

### Pour les Recruteurs

1. Aller dans "Détails du Poste"
2. Dans la liste des candidats, cliquer sur "Évaluer Quiz"
3. Le système génère automatiquement un quiz basé sur les compétences requises
4. Le candidat reçoit une notification

### Pour les Candidats

1. Voir le bouton quiz (icône question) près de la cloche de notification
2. Cliquer pour voir les quiz assignés
3. Cliquer sur "Passer Quiz" pour commencer
4. Répondre aux questions et soumettre

## Avantages

1. **Personnalisation** : Quiz adaptés aux besoins spécifiques du poste
2. **Évaluation Ciblée** : Questions basées sur les compétences réellement requises
3. **Flexibilité** : Possibilité d'assigner des quiz à des candidats spécifiques
4. **Suivi** : Traçabilité complète des assignations et résultats
5. **Interface Moderne** : Design cohérent avec le reste de l'application

## Configuration

Pour activer le système :

1. Exécuter le script de migration : `python init_quiz_db.py`
2. Redémarrer l'application
3. Les boutons apparaîtront automatiquement dans les interfaces

## Notes Techniques

- Le système utilise le même générateur de quiz existant mais avec des paramètres différents
- Les quiz sont générés à la demande pour éviter la répétition
- L'interface est responsive et fonctionne sur mobile
- Les notifications sont gérées via WebSocket pour les mises à jour en temps réel
