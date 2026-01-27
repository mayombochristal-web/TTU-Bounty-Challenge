import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.integrate import solve_ivp
import base64
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="TTU MC³ - Phase Key Decoder", layout="wide")

# --- PARAMÈTRES MAÎTRES TTU (Source: Analyse CERN/TTU) ---
PHI_M_REF = 0.839119
PHI_C_REF = 0.779739
PHI_D_REF = 0.732220
K_CURVATURE = -321434.8527

# --- LOGIQUE SCIENTIFIQUE (Système Dynamique MC³) ---
def ttu_system(t, y, phi_c_input):
    pm, pc, pd = y
    # Paramètres de potentiel assurant les bifurcations
    a, b = -1.0, 1.0
    lambda_mcd = 1.2
    eta_d = 0.8 # Coefficient de dissipation
    
    # Équations d'évolution Triadique
    dpm = -(2*a*pm + 4*b*pm**3) + lambda_mcd * pc * pd
    dpc = -(2*(-0.5)*pc + 4*0.8*pc**3) + lambda_mcd * pm * pd
    
    # La déviance de phase injectée par l'utilisateur perturbe la dissipation via K
    error = abs(phi_c_input - PHI_C_REF)
    dpd = -(2*(-0.3)*pd + 4*0.5*pd**3) + lambda_mcd * pm * pc - eta_d * pd + (error * K_CURVATURE)
    
    return [dpm, dpc, dpd]

# --- FONCTION DE GÉNÉRATION DE CERTIFICAT ---
def generate_certificate(phase):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cert_text = f"""
    --- CERTIFICAT DE RÉSONANCE TTU ---
    STATUT : PHASE SYNCHRONISÉE
    HORODATAGE : {timestamp}
    CLÉ DE PHASE (PHI_C) : {phase}
    RÉGIME : COHÉRENCE QUANTIQUE DOMINANTE
    COURBURE K : {K_CURVATURE}
    ----------------------------------
    """
    b64 = base64.b64encode(cert_text.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="TTU_Certificate.txt" style="text-decoration:none;"><button style="background-color:#00ff00;border:none;color:black;padding:10px 20px;text-align:center;text-decoration:none;display:inline-block;font-size:16px;margin:4px 2px;cursor:pointer;border-radius:8px;font-weight:bold;">📥 Télécharger le Certificat de Résonance</button></a>'

# --- INTERFACE UTILISATEUR ---
st.title("🌌 TTU MC³ : Dashboard de Phase Event Horizon")
st.markdown(f"**Analyseur de Flot Triadique - Constante de Courbure K = {K_CURVATURE}**")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Console de Contrôle")
    phi_c_user = st.number_input("Entrer la Clé de Phase (ΦC)", value=0.000000, format="%.6f")
    
    # Calcul de la résonance
    resonance = 1.0 - min(abs(phi_c_user - PHI_C_REF) * 100, 1.0)
    
    st.metric("Indice de Résonance", f"{resonance*100:.4f}%")
    
    if resonance > 0.9999:
        st.success("✅ ÉTAT : RÉSONANCE - Flux Déchiffré")
        st.info("Message : 'Le temps est un flux irréversible.'")
        st.markdown(generate_certificate(phi_c_user), unsafe_allow_html=True)
    else:
        st.error("❌ ÉTAT : DÉCOHÉRENCE - Bruit Hyperbolique")
        st.warning("La trajectoire diverge sous l'effet de la courbure K.")

with col2:
    # Simulation
    y0 = [0.2, 0.1, 0.3]
    t_eval = np.linspace(0, 100, 5000)
    sol = solve_ivp(ttu_system, (0, 100), y0, t_eval=t_eval, args=(phi_c_user,))
    
    # Tracé Plotly
    fig = go.Figure(data=[go.Scatter3d(
        x=sol.y[0], y=sol.y[1], z=sol.y[2],
        mode='lines',
        line=dict(color='cyan' if resonance > 0.99 else 'red', width=2)
    )])
    
    fig.update_layout(
        scene=dict(xaxis_title='ΦM', yaxis_title='ΦC', zaxis_title='ΦD'),
        margin=dict(l=0, r=0, b=0, t=0),
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
