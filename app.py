import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.integrate import solve_ivp
import base64
import hashlib
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="TTU MC³ - Stealth Vault v2", layout="wide")

# --- PARAMÈTRES MAÎTRES TTU (Vérifiés CERN) ---
PHI_C_REF = 0.779739
K_CURVATURE = -321434.8527

# --- LOGIQUE SCIENTIFIQUE (Système Dynamique MC³) ---
def ttu_system(t, y, phi_c_input):
    pm, pc, pd = y
    a, b = -1.0, 1.0
    lambda_mcd = 1.2
    eta_d = 0.8
    
    dpm = -(2*a*pm + 4*b*pm**3) + lambda_mcd * pc * pd
    dpc = -(2*(-0.5)*pc + 4*0.8*pc**3) + lambda_mcd * pm * pd
    
    error = abs(phi_c_input - PHI_C_REF)
    dpd = -(2*(-0.3)*pd + 4*0.5*pd**3) + lambda_mcd * pm * pc - eta_d * pd + (error * K_CURVATURE)
    
    return [dpm, dpc, dpd]

# --- INTERFACE UTILISATEUR ---
st.title("🌌 TTU MC³ : Dashboard de Phase & Coffre-fort")
st.markdown(f"**Moteur de Chiffrement Géométrique - Courbure K = {K_CURVATURE}**")

st.info("""
**Comment ça marche ?** Ce système ne repose pas sur un mot de passe classique. Il utilise une simulation de physique avancée. 
1. Si la **Clé de Phase** est fausse, l'univers est chaotique (Rouge). 
2. Si la **Clé de Phase** est exacte (Résonance), l'univers s'ordonne (Cyan).
Seul l'ordre permet de lire le message caché.
""")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Synchronisation")
    st.write("Ajustez la phase pour stabiliser l'attracteur à droite.")
    phi_c_user = st.number_input("Clé de Phase ΦC (Essayez 0.779739)", value=0.0, format="%.6f")
    resonance = 1.0 - min(abs(phi_c_user - PHI_C_REF) * 100, 1.0)
    st.metric("Niveau de Résonance", f"{resonance*100:.4f}%")
    
    if resonance > 0.9999:
        st.success("✅ RÉSONANCE ÉTABLIE : La forme est stable.")
    else:
        st.error("❌ DÉCOHÉRENCE : Le système est instable.")

# --- SIMULATION ---
y0 = [0.2, 0.1, 0.3]
t_eval = np.linspace(0, 100, 5000)
sol = solve_ivp(ttu_system, (0, 100), y0, t_eval=t_eval, args=(phi_c_user,))

with col2:
    st.subheader("2. Signature Géométrique")
    fig = go.Figure(data=[go.Scatter3d(x=sol.y[0], y=sol.y[1], z=sol.y[2], mode='lines', line=dict(color='cyan' if resonance > 0.99 else 'red', width=2))])
    fig.update_layout(scene=dict(xaxis_title='Mémoire', yaxis_title='Cohérence', zaxis_title='Dissipation'), margin=dict(l=0, r=0, b=0, t=0), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# --- MODULE COFFRE-FORT (CHIFFREMENT & DÉCHIFFREMENT) ---
st.divider()
st.header("🔐 3. Coffre-fort à Résonance")

tab1, tab2 = st.tabs(["🔒 Chiffrer (Cacher)", "🔓 Déchiffrer (Retrouver)"])

# Extraction de la signature géométrique actuelle (Clé dynamique)
signature = sol.y[:, -500:].tobytes()
ttu_key = hashlib.sha256(signature).digest()

with tab1:
    st.write("Écrivez un secret. Il sera mélangé à la forme géométrique actuelle.")
    msg_to_encrypt = st.text_area("Message à protéger", "Le temps est un flux irréversible.")
    if st.button("Lancer le Chiffrement"):
        msg_bytes = msg_to_encrypt.encode()
        ciphertext = bytes([b ^ ttu_key[i % len(ttu_key)] for i, b in enumerate(msg_bytes)])
        st.subheader("Votre code secret (Ciphertext) :")
        st.code(ciphertext.hex(), language="text")
        st.warning("⚠️ Attention : Si vous changez la phase maintenant, ce code deviendra illisible !")

with tab2:
    st.write("Collez un code secret ici pour tenter de le lire.")
    cipher_to_decrypt = st.text_input("Coller le code hexadécimal ici")
    if st.button("Tenter le Déchiffrement"):
        try:
            cipher_bytes = bytes.fromhex(cipher_to_decrypt)
            decrypted_bytes = bytes([b ^ ttu_key[i % len(ttu_key)] for i, b in enumerate(cipher_bytes)])
            
            if resonance > 0.9999:
                st.subheader("✅ Message Décodé :")
                st.success(decrypted_bytes.decode(errors="ignore"))
                st.balloons()
            else:
                st.subheader("❌ Échec :")
                st.warning(f"Bruit détecté : {decrypted_bytes.hex()[:20]}...")
                st.error("La phase est incorrecte. La 'clé géométrique' ne correspond pas au verrou.")
        except Exception as e:
            st.error("Le code collé n'est pas valide.")

st.caption("Projet TTU Event Horizon - Sécurité basée sur la physique des systèmes non-linéaires.")
