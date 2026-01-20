# 🚁 IoD-Sim Scenario Editor

**Éditeur graphique (GUI) pour créer et modifier des scénarios de simulation pour  
[IoD-Sim](https://github.com/iod-sim/iod-sim) — *Internet of Drones Simulator*.**

![Version](https://img.shields.io/badge/Version-0.1-orange)
![Status](https://img.shields.io/badge/Status-Work_in_Progress-yellow)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## État du projet (v0.1)

Ce projet est actuellement en **phase de développement initial (version 0.1)**.  
Il est fonctionnel pour charger, éditer et sauvegarder des scénarios IoD-Sim, mais certaines fonctionnalités restent à implémenter.

### ✅ Fonctionnalités disponibles
- Chargement et sauvegarde de fichiers **JSON compatibles IoD-Sim**
- Édition dynamique des entités :
  - Drones
  - Bâtiments
  - Configuration réseau
- Gestion des listes :
  - Ajout / suppression de nœuds
  - Logs
  - Configurations statiques
- Validation basique des types via l’interface

---

## 📋 Prérequis

Pour utiliser l’éditeur, vous devez disposer de :

1. **Python 3.8** ou supérieur
2. La bibliothèque **PySide6** (Qt for Python)

---

## 🚀 Installation & Lancement

### 1️⃣ Cloner ou télécharger le projet

Structure de fichiers recommandée :

```text
iod_sim_editor/
├── main.py
├── README.md
├── backend/
│   ├── __init__.py
│   ├── models.py        # Définitions des données (dataclasses)
│   └── serializer.py    # Gestion Import / Export JSON
└── ui/
    ├── __init__.py
    ├── main_window.py   # Fenêtre principale
    ├── utils.py         # Fonctions utilitaires
    └── widgets/
        ├── __init__.py
        ├── auto_form.py     # Formulaire dynamique
        └── list_editor.py   # Gestionnaire de listes
```

### 2️⃣ Créer un environnement virtuel (recommandé)
Cela évite de polluer l’installation Python globale.

🪟 Windows
```text bash
python -m venv venv
.\venv\Scripts\activate
```

🐧 macOS / Linux
```text bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Installer les dépendances
```text bash
Copier le code
pip install PySide6
```

### 4️⃣ Lancer l’application
```text bash
python main.py
```

## 📖 Utilisation
Ouvrir un scénario
File > Open puis sélectionnez un fichier JSON IoD-Sim existant
(ex. wifi_gps_spoofing.json).

Naviguer
Utilisez l’arborescence à gauche pour sélectionner une catégorie
(ex. Drones) ou un objet spécifique.

Éditer
Modifiez les valeurs dans le panneau de droite.
Les changements sont appliqués immédiatement en mémoire.

Ajouter / Supprimer
Pour les listes (Buildings, Drones, Logs), sélectionnez le dossier parent puis cliquez sur Ajouter (+).

Utilisez le bouton X pour supprimer un élément.

Sauvegarder

## 🛠️ Architecture Technique
Le projet repose sur une architecture modulaire séparant clairement la logique métier de l’interface graphique.

Backend (backend/)
Dataclasses Python reflétant la structure C++ de ns-3

Gestion des conversions complexes :

snake_case ↔ PascalCase

Garantit la compatibilité totale avec IoD-Sim

Interface Graphique (ui/)
Génération automatique des formulaires via introspection

Support de nouveaux modules ns-3 sans modification de l’UI

Interface évolutive et maintenable