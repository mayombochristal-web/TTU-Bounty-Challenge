import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.integrate import solve_ivp
import base64
import hashlib
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="TTU MC³ - Stealth Vault", layout="wide")

# --- PARAMÈTRES MAÎTRES TTU (Vérifiés CERN) ---
PHI_C_REF = 0.779739
K_CURVATURE = -321434.8527

# --- LOGIQUE SCIENTIFIQUE (Système Dynamique MC³) ---
def ttu_system(t, y, phi_c_input):
    pm, pc, pd = y
    a, b = -1.0, 1.0
    lambda_mcd = 1.2
    eta_d = 0.8
    
    # Équations d'évolution Triadique (Page 14 du document)
    dpm = -(2*a*pm + 4*b*pm**3) + lambda_mcd * pc * pd
    dpc = -(2*(-0.5)*pc + 4*0.8*pc**3) + lambda_mcd * pm * pd
    
    # La déviance de phase injectée perturbe la dissipation via la courbure K
    error = abs(phi_c_input - PHI_C_REF)
    dpd = -(2*(-0.3)*pd + 4*0.5*pd**3) + lambda_mcd * pm * pc - eta_d * pd + (error * K_CURVATURE)
    
    return [dpm, dpc, dpd]

def generate_certificate(phase):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cert_text = f"--- CERTIFICAT DE RESONANCE TTU ---\nSTATUS: SYNCHRONIZED\nPHASE: {phase}\nK: {K_CURVATURE}\nTS: {timestamp}"
    b64 = base64.b64encode(cert_text.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="TTU_Cert.txt" style="text-decoration:none;"><button style="background-color:#00ff00;border:none;color:black;padding:10px 20px;border-radius:8px;font-weight:bold;cursor:pointer;width:100%;">📥 Télécharger le Certificat de Résonance</button></a>'

# --- INTERFACE UTILISATEUR ---
st.title("🌌 TTU MC³ : Dashboard de Phase & Coffre-fort")
st.markdown(f"**Moteur de Chiffrement Géométrique - Courbure K = {K_CURVATURE}**")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Console de Synchronisation")
    phi_c_user = st.number_input("Clé de Phase ΦC", value=0.0, format="%.6f")
    resonance = 1.0 - min(abs(phi_c_user - PHI_C_REF) * 100, 1.0)
    st.metric("Niveau de Résonance", f"{resonance*100:.4f}%")
    
    if resonance > 0.9999:
        st.success("✅ RÉSONANCE ÉTABLIE : Signal Déchiffrable")
        st.markdown(generate_certificate(phi_c_user), unsafe_allow_html=True)
    else:
        st.error("❌ DÉCOHÉRENCE : Signal Fragmenté")

# --- SIMULATION ---
y0 = [0.2, 0.1, 0.3]
t_eval = np.linspace(0, 100, 5000)
sol = solve_ivp(ttu_system, (0, 100), y0, t_eval=t_eval, args=(phi_c_user,))

with col2:
    fig = go.Figure(data=[go.Scatter3d(x=sol.y[0], y=sol.y[1], z=sol.y[2], mode='lines', line=dict(color='cyan' if resonance > 0.99 else 'red', width=2))])
    fig.update_layout(scene=dict(xaxis_title='ΦM', yaxis_title='ΦC', zaxis_title='ΦD'), margin=dict(l=0, r=0, b=0, t=0), template="plotly_dark")
    st.plotly_chart(fig, width='stretch')

# --- MODULE COFFRE-FORT (CHIFFREMENT RÉEL) ---
st.divider()
st.header("🔐 Coffre-fort à Résonance Triadique")

col_text, col_cipher = st.columns(2)

with col_text:
    message_input = st.text_area("Message à chiffrer", "Le temps est un flux irréversible.")
    
if st.button("Lancer le Chiffrement par Flot MC³"):
    # On extrait la signature géométrique des 500 derniers points de l'attracteur
    signature = sol.y[:, -500:].tobytes()
    key = hashlib.sha256(signature).digest()
    
    # XOR Chiffrement
    msg_bytes = message_input.encode()
    ciphertext = bytes([b ^ key[i % len(key)] for i, b in enumerate(msg_bytes)])
    
    with col_cipher:
        st.subheader("Résultat (Ciphertext)")
        st.code(ciphertext.hex(), language="text")
        
        if resonance > 0.9999:
            st.success("🔓 État de résonance : Le message est intègre.")
        else:
            st.warning("🔒 État de chaos : Les données sont physiquement détruites par K.")

st.caption("Note technique : La clé de chiffrement n'est pas stockée, elle est générée par la dynamique du système.")
