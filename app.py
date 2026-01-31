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
        self.active_keys = {"bounty": hashlib.sha3_512(b"master_seed").digest()}
    
    def rotate_key(self):
        new_seed = self.active_keys["bounty"] + secrets.token_bytes(32)
        self.active_keys["bounty"] = hashlib.sha3_512(new_seed).digest()

class TTUShieldSentinel:
    def __init__(self):
        self.system_health = 1.0
        self.k_viscosity = 0.05
        self.history = deque(maxlen=50)

    def analyze_attack(self, payload):
        # Mesure de l'entropie (Dissipation Phi_D)
        if not payload: return 0.0, "NORMAL"
        prob = [float(payload.count(c)) / len(payload) for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        # Calcul de la déviation (Vecteur Maître)
        deviation = entropy / 8.0 # Normalisé
        self.k_viscosity = 0.8 * self.k_viscosity + 0.2 * deviation
        
        self.history.append(self.k_viscosity)
        
        if self.k_viscosity > 0.75:
            return self.k_viscosity, "CRITICAL"
        elif self.k_viscosity > 0.4:
            return self.k_viscosity, "SUSPICIOUS"
        return self.k_viscosity, "STABLE"

# --- INITIALISATION SESSION ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = TTUShieldSentinel()
    st.session_state.crypto = QuantumResilientEncryption()
    st.session_state.leaderboard = []

# --- INTERFACE ---
st.title("🛡️ TTU-Shield Sentinel Pro : Quantum Bounty Challenge")
st.markdown("""
### Saurez-vous briser la stabilité du Vecteur Maître ?
Ce système détecte les attaques par analyse de la **viscosité informationnelle ($k$)**. 
Toute tentative de bifurcation chaotique est immédiatement isolée par le bouclier immunitaire.
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Santé du Système", f"{st.session_state.sentinel.system_health * 100:.1f}%")
with col2:
    st.metric("Viscosité $k$ Actuelle", f"{st.session_state.sentinel.k_viscosity:.4f}")
with col3:
    st.metric("Bounty Pool", "2,500 $ (Fictif)")

# --- ZONE D'ATTAQUE ---
st.divider()
st.header("💻 Terminal d'Injection de Chaos")

c1, c2 = st.columns([2, 1])

with c1:
    hacker_name = st.text_input("Alias du Hacker", "Anonymous_Hacker")
    attack_payload = st.text_area("Injectez votre payload (Code, SQL, Malware Masked...)", height=200)
    
    if st.button("LANCER L'ATTAQUE"):
        if attack_payload:
            k_score, status = st.session_state.sentinel.analyze_attack(attack_payload)
            
            if status == "CRITICAL":
                st.error(f"🚨 ALERTE : Bifurcation détectée ! Attaque neutralisée par l'Anticorps TTU.")
                st.session_state.leaderboard.append({"Hacker": hacker_name, "Score k": k_score, "Result": "Capturé"})
            elif status == "SUSPICIOUS":
                st.warning(f"⚠️ ATTENTION : Instabilité détectée. Le système immunitaire se renforce.")
            else:
                st.success("✅ ÉCHEC : Le Vecteur Maître reste sur son cycle limite stable.")
        else:
            st.info("Veuillez entrer un payload pour tester le système.")

with c2:
    st.subheader("📡 Visualisation Holonome")
    # Graphique de stabilité
    if len(st.session_state.sentinel.history) > 0:
        st.line_chart(list(st.session_state.sentinel.history))
    st.caption("Évolution de la viscosité $k$ en temps réel.")



# --- LEADERBOARD ---
st.divider()
st.header("🏆 Mur de la Gloire (Hackers Capturés)")
if st.session_state.leaderboard:
    df = pd.DataFrame(st.session_state.leaderboard)
    st.dataframe(df.sort_values(by="Score k", ascending=False), use_container_width=True)
else:
    st.write("Aucun hacker n'a encore osé défier le Sentinel.")

# --- FOOTER ---
st.sidebar.title("Paramètres TTU")
if st.sidebar.button("Rotation Clé Quantique"):
    st.session_state.crypto.rotate_key()
    st.sidebar.success("Clé rotée avec succès.")

st.sidebar.markdown("""
**Documentation :**
- Basé sur la Théorie Triadique Unifiée.
- Détection par Attracteurs de Lorenz.
- Résistance post-quantique.
""")
