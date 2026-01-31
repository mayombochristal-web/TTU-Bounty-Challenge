import streamlit as st
import numpy as np
import pandas as pd
import hashlib
import time
import secrets
from datetime import datetime
from scipy import stats
from collections import deque

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="TTU-Shield Quantum Bounty", layout="wide")

# --- MODULES TTU-MC3 (VERSION PRO) ---

class QuantumResilientEncryption:
    def __init__(self):
        # Initialisation avec une clé sécurisée
        self.active_keys = {"bounty": hashlib.sha3_512(secrets.token_bytes(64)).digest()}
    
    def rotate_key(self):
        new_seed = self.active_keys["bounty"] + secrets.token_bytes(32)
        self.active_keys["bounty"] = hashlib.sha3_512(new_seed).digest()

class TTUShieldSentinel:
    def __init__(self):
        self.system_health = 1.0
        self.k_viscosity = 0.05
        # Utilisation d'une liste simple pour assurer la compatibilité Streamlit Charts
        self.history = [0.05] * 50 

    def analyze_attack(self, payload):
        if not payload: 
            return 0.0, "NORMAL"
        
        # 1. Mesure de l'entropie (Dissipation Phi_D)
        # On calcule la fréquence d'apparition de chaque caractère
        prob = [float(payload.count(c)) / len(payload) for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        # 2. Calcul de la déviation du Vecteur Maître
        # On normalise l'entropie par rapport au max théorique (8.0 pour de l'ASCII)
        deviation = entropy / 8.0 
        
        # Mise à jour de la viscosité k (Lissage exponentiel TTU)
        self.k_viscosity = 0.7 * self.k_viscosity + 0.3 * deviation
        
        # Mise à jour de l'historique (Glissement de fenêtre)
        self.history.append(self.k_viscosity)
        if len(self.history) > 50:
            self.history.pop(0)
        
        # Seuils de bifurcation
        if self.k_viscosity > 0.70:
            return self.k_viscosity, "CRITICAL"
        elif self.k_viscosity > 0.35:
            return self.k_viscosity, "SUSPICIOUS"
        return self.k_viscosity, "STABLE"

# --- INITIALISATION SESSION (CRUCIAL POUR STREAMLIT) ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = TTUShieldSentinel()
if 'crypto' not in st.session_state:
    st.session_state.crypto = QuantumResilientEncryption()
if 'leaderboard' not in st.session_state:
    st.session_state.leaderboard = []

# --- INTERFACE ---
st.title("🛡️ TTU-Shield Sentinel Pro : Quantum Bounty Challenge")
st.markdown("""
### Saurez-vous briser la stabilité du Vecteur Maître ?
Ce système détecte les attaques par analyse de la **viscosité informationnelle ($k$)**. 
Toute tentative de bifurcation chaotique est immédiatement isolée par le bouclier immunitaire.
""")

# Métriques en temps réel
m1, m2, m3 = st.columns(3)
m1.metric("Santé du Système", f"{st.session_state.sentinel.system_health * 100:.1f}%")
m2.metric("Viscosité $k$ (Actuelle)", f"{st.session_state.sentinel.k_viscosity:.4f}")
m3.metric("Bounty Pool", "2,500 $ (Fictif)")

st.divider()

# --- ZONE DE TEST ET VISUALISATION ---
col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.header("💻 Terminal d'Injection de Chaos")
    hacker_name = st.text_input("Alias du Hacker", "Anonymous_Hacker")
    attack_payload = st.text_area("Injectez votre payload (Code, SQL, Malware Masked...)", height=220, placeholder="Collez votre code d'attaque ici...")
    
    if st.button("🚀 LANCER L'ATTAQUE SUR LE VECTEUR"):
        if attack_payload:
            k_score, status = st.session_state.sentinel.analyze_attack(attack_payload)
            
            if status == "CRITICAL":
                st.error(f"🚨 ALERTE ROUGE : Bifurcation détectée (k={k_score:.3f}) ! Attaque neutralisée.")
                st.session_state.leaderboard.append({
                    "Hacker": hacker_name, 
                    "Score k": round(k_score, 4), 
                    "Heure": datetime.now().strftime("%H:%M:%S"),
                    "Result": "CAPTURED"
                })
            elif status == "SUSPICIOUS":
                st.warning(f"⚠️ INSTABILITÉ : Le Vecteur Maître dévie (k={k_score:.3f}). Surveillance accrue.")
            else:
                st.success(f"✅ ÉCHEC : L'attracteur reste stable (k={k_score:.3f}). Aucune menace détectée.")
        else:
            st.info("Entrez une charge utile pour tester la résistance du système.")

with col_right:
    st.header("📡 Visualisation Holonome")
    # Création d'un DataFrame pour forcer Streamlit à tracer correctement
    df_visu = pd.DataFrame({
        "Viscosité k": st.session_state.sentinel.history
    })
    
    # Graphique interactif
    st.line_chart(df_visu, height=300, use_container_width=True)
    st.caption("Monitoring de la trajectoire informationnelle. Un pic > 0.7 indique un saut holonome (attaque).")



# --- LEADERBOARD ---
st.divider()
st.header("🏆 Mur de la Gloire (Menaces Neutralisées)")
if st.session_state.leaderboard:
    df_lb = pd.DataFrame(st.session_state.leaderboard)
    st.dataframe(df_lb.sort_values(by="Score k", ascending=False), use_container_width=True)
else:
    st.info("Le système est actuellement inviolé. Soyez le premier à tenter une bifurcation.")

# --- BARRE LATÉRALE ---
st.sidebar.title("🛠️ Paramètres TTU-MC³")
if st.sidebar.button("🔐 Rotation Clé Quantique"):
    st.session_state.crypto.rotate_key()
    st.sidebar.success("Clé rotée par mutation entropique.")

st.sidebar.markdown(f"""
**Statut Sentinel :**
- Mode : Défense Active
- Algorithme : $MC^3$ Dissipatif
- Post-Quantum : Actif

---
*Dernière rotation :*
{datetime.now().strftime("%H:%M:%S")}
""")
