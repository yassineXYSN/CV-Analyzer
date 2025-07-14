# 🎭 Système de Détection d'Émotions en Temps Réel

## 📋 Fonctionnalités

Ce système permet de détecter les émotions en temps réel pendant la transcription audio. Voici les fonctionnalités principales :

### ✨ Fonctionnalités Principales

1. **Transcription en temps réel** avec reconnaissance vocale
2. **Détection d'émotions** basée sur l'analyse de mots-clés
3. **Affichage visuel** des émotions détectées avec icônes et couleurs
4. **Statistiques d'émotions** en temps réel
5. **Indicateur d'émotion en cours** avec animation
6. **Stockage des données** en base de données

### 🎯 Émotions Détectées

- **😊 Joie** : heureux, content, joyeux, excellent, super, génial, fantastique, merveilleux
- **😢 Tristesse** : triste, déprimé, malheureux, désolé, déçu, découragé
- **😠 Colère** : fâché, en colère, furieux, irrité, énervé, exaspéré
- **😨 Peur** : peur, effrayé, inquiet, anxieux, stressé, paniqué
- **😲 Surprise** : surpris, étonné, stupéfait, incroyable, wow
- **😐 Neutre** : normal, ok, bien, correct, standard

## 🚀 Comment Utiliser

### 1. Démarrer l'Application

```bash
cd mon-projet-flask
python app.py
```

### 2. Accéder à l'Entretien

1. Allez sur `http://localhost:5000`
2. Créez un utilisateur et réservez un créneau
3. Cliquez sur le lien d'entretien

### 3. Utiliser la Détection d'Émotions

1. **Démarrer la transcription** : Cliquez sur "🎙️ Démarrer Transcription"
2. **Parler** : Le système détectera automatiquement vos émotions
3. **Voir les résultats** : Les émotions s'affichent en temps réel avec des icônes colorées
4. **Statistiques** : Consultez les statistiques d'émotions en bas de page

## 🔧 Configuration

### Dépendances Requises

```bash
pip install -r requirements.txt
```

### Base de Données

Le système utilise MySQL. Assurez-vous que :
- MySQL est installé et en cours d'exécution
- La base de données `mon_projet_flask` existe
- Les tables sont créées automatiquement au démarrage

### Variables d'Environnement

```python
# Dans app.py
ASSEMBLYAI_API_KEY = "votre_clé_api"  # Pour transcription avancée
MAIL_USERNAME = "votre_email@gmail.com"
MAIL_PASSWORD = "votre_mot_de_passe_app"
```

## 📊 Fonctionnalités Techniques

### Analyse d'Émotions

Le système utilise une analyse basée sur des mots-clés :

```python
def analyze_emotions(text):
    emotions = {
        'joy': ['heureux', 'content', 'joyeux', 'excellent'],
        'sadness': ['triste', 'déprimé', 'malheureux'],
        # ... autres émotions
    }
    # Analyse du texte et retour des émotions détectées
```

### Stockage des Données

- **Transcription** : Stockée dans `TimeSlot.transcription`
- **Émotions** : Stockées en JSON dans `TimeSlot.emotions_data`
- **Statistiques** : Calculées en temps réel

### Communication en Temps Réel

- **SocketIO** : Pour les mises à jour en temps réel
- **WebSocket** : Pour la communication bidirectionnelle
- **Threading** : Pour la transcription en arrière-plan

## 🎨 Interface Utilisateur

### Éléments Visuels

1. **Icônes d'émotions** : 😊 😢 😠 😨 😲 😐
2. **Couleurs** : Chaque émotion a sa couleur distinctive
3. **Animations** : Effets de pulsation pour les nouvelles détections
4. **Statistiques** : Graphiques en temps réel

### Responsive Design

- Interface adaptée mobile et desktop
- Boutons et contrôles optimisés
- Affichage adaptatif des statistiques

## 🔍 Dépannage

### Problèmes Courants

1. **Microphone non détecté**
   - Vérifiez les permissions du navigateur
   - Assurez-vous que le microphone est connecté

2. **Transcription ne fonctionne pas**
   - Vérifiez la connexion Internet
   - Assurez-vous que SpeechRecognition est installé

3. **Émotions non détectées**
   - Parlez clairement et distinctement
   - Utilisez des mots-clés d'émotions

### Logs

Les logs sont disponibles dans `app.log` :
```bash
tail -f app.log
```

## 🚀 Améliorations Futures

1. **IA avancée** : Intégration de modèles d'IA pour une meilleure détection
2. **Analyse tonale** : Détection basée sur le ton de voix
3. **Machine Learning** : Apprentissage automatique des patterns émotionnels
4. **Export des données** : Export des statistiques en PDF/Excel
5. **API REST** : Endpoints pour intégration externe

## 📝 Notes Techniques

- **Performance** : Optimisé pour la détection en temps réel
- **Sécurité** : Validation des données et protection contre les injections
- **Scalabilité** : Architecture modulaire pour faciliter les extensions
- **Maintenance** : Code commenté et structuré

## 🤝 Contribution

Pour contribuer au projet :

1. Fork le repository
2. Créez une branche pour votre fonctionnalité
3. Testez vos modifications
4. Soumettez une pull request

## 📞 Support

Pour toute question ou problème :
- Vérifiez les logs dans `app.log`
- Consultez la documentation technique
- Ouvrez une issue sur GitHub

---

**Développé avec ❤️ pour la détection d'émotions en temps réel** 