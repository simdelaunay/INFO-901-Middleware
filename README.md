# INFO-901-Middleware

## Lancer le projet

python Launcher.py

# Middleware Distribué pour Systèmes de Communication Asynchrone

Ce projet implémente un middleware distribué en Python conçu pour faciliter la communication asynchrone entre processus distribués dans un système. Le middleware utilise des horloges de Lamport pour maintenir la cohérence des messages et prend en charge la synchronisation des processus et la gestion des sections critiques.

## Caractéristiques

- **Communication Asynchrone et Synchrone** : Permet aux processus de communiquer de manière asynchrone sans attendre les réponses immédiates et de manière synchrone avec attente de réponses.
- **Gestion des Sections Critiques** : Utilise un token circulant dans le système pour permettre un accès exclusif aux sections critiques.
- **Synchronisation des Processus** : Permet la synchronisation de tous les processus avant de procéder à des opérations critiques.
- **Gestion Dynamique des Identifiants de Processus** : Attribue et gère les identifiants de manière dynamique pour chaque processus participant au système.
- **Détection de la Panne** : Intègre un mécanisme de heartbeat pour détecter les défaillances des processus et ajuster les opérations en conséquence.

## Dépendances

Ce projet repose sur les bibliothèques Python suivantes :

- `pyeventbus3` : Pour la gestion des événements dans le système.
- `threading` : Pour la gestion des threads en Python.

## Installation

Clonez le dépôt sur votre machine locale :

```bash
git clone https://github.com/votre_nom_utilisateur/votre_projet.git
cd votre_projet

```
