# TTU BASTION EDR – Cyber‑Résilience par Membrane Adaptive

Bienvenue dans le dépôt officiel de **TTU BASTION EDR**, la première plateforme de cyber‑défense qui traite l’information comme un flux thermodynamique.  
Notre noyau **TTU‑MC³** (Memory, Coherence, Core) utilise un modèle de courbure \( k \) pour absorber les pics de charge, dissiper les menaces et garantir une stabilité permanente – même sous attaque.

> **Supérieur aux solutions statiques** : Là où Kaspersky ou Avast se contentent de signatures, nous utilisons une **Membrane Adaptive** qui contracte ou relâche la sécurité en temps réel, comme un organisme vivant.

---

## ✨ Fonctionnalités clés

- **Dissipation dynamique** : toutes les données transitent par un vault avant d’être traitées, évitant les saturations.
- **Courbure \(k\)** : mesure instantanée de la charge système, ajuste les seuils de sécurité.
- **Battement de cœur** : modulation globale toutes les 60 secondes.
- **Quotas intelligents** : 3 analyses gratuites, puis abonnement mensuel avec facturation à la consommation.
- **Traçabilité** : chaque ligne reçoit la signature `sync_k` pour audit et preuve d’intégrité.
- **Détection Zero‑Day** : basée sur l’impact thermodynamique, pas sur des signatures.

---

## 🚀 Déploiement rapide

### Prérequis

- Supabase (projet avec pg_cron activé)
- Python 3.9+
- Compte [Resend](https://resend.com) pour les emails
- Compte [Flutterwave](https://flutterwave.com) pour les paiements (optionnel)

### 1. Base de données

Exécutez le script [`core/schema.sql`](core/schema.sql) dans l’éditeur SQL de Supabase.  
Ce script crée toutes les tables, fonctions et triggers nécessaires.

### 2. Edge Functions

Déployez les deux fonctions Supabase :

```bash
supabase functions deploy signup --no-verify-jwt
supabase functions deploy check-expired-trials --no-verify-jwt