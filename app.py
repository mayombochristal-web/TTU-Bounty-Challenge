import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.integrate import solve_ivp
import base64
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="TTU MC³ - Event Horizon", layout="wide")

# --- PARAMÈTRES MAÎTRES TTU (Vérifiés CERN) ---
PHI_M_REF = 0.839119
PHI_C_REF = 0.779739
PHI_D_REF = 0.732220
K_CURVATURE = -321434.8527

# --- SYSTÈME DYNAMIQUE ---
def ttu_system(t, y, phi_c_input):
    pm, pc, pd = y
    a, b = -1.0, 1.0
    lambda_mcd = 1.2
    eta_d = 0.8
    
    dpm = -(2*a*pm + 4*b*pm**3) + lambda_mcd * pc * pd
    dpc = -(2*(-0.5)*pc + 4*0.8*pc**3) + lambda_mcd * pm * pd
    
    # Courbure K agissant sur la dissipation
    error = abs(phi_c_input - PHI_C_REF)
    dpd = -(2*(-0.3)*pd + 4*0.5*pd**3) + lambda_mcd * pm * pc - eta_d * pd + (error * K_CURVATURE)
    
    return [dpm, dpc, dpd]

def generate_certificate(phase):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cert_text = f"--- CERTIFICAT DE RESONANCE TTU ---\nSTATUT : PHASE SYNCHRONISEE\nDATE : {timestamp}\nCLE : {phase}\nCOURBURE : {K_CURVATURE}\n----------------------------------"
    b64 = base64.b64encode(cert_text.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="TTU_Cert.txt" style="text-decoration:none;"><button style="background-color:#00ff00;border:none;color:black;padding:10px 20px;border-radius:8px;font-weight:bold;cursor:pointer;width:100%;">📥 Télécharger le Certificat Officiel</button></a>'

# --- INTERFACE ---
st.title("🌌 TTU MC³ : Dashboard de Phase Event Horizon")
st.markdown(f"**Analyseur de Flot Triadique - K = {K_CURVATURE}**")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Console de Contrôle")
    phi_c_user = st.number_input("Entrer la Clé de Phase (ΦC)", value=0.0, format="%.6f")
    resonance = 1.0 - min(abs(phi_c_user - PHI_C_REF) * 100, 1.0)
    st.metric("Indice de Résonance", f"{resonance*100:.4f}%")
    
    if resonance > 0.9999:
        st.success("✅ RÉSONANCE ÉTABLIE")
        st.info("Flux stable détecté : 'Le temps est un flux irréversible.'")
        st.markdown(generate_certificate(phi_c_user), unsafe_allow_html=True)
    else:
        st.error("❌ ÉTAT : DÉCOHÉRENCE")

with col2:
    y0 = [0.2, 0.1, 0.3]
    t_eval = np.linspace(0, 100, 5000)
    sol = solve_ivp(ttu_system, (0, 100), y0, t_eval=t_eval, args=(phi_c_user,))
    fig = go.Figure(data=[go.Scatter3d(x=sol.y[0], y=sol.y[1], z=sol.y[2], mode='lines', line=dict(color='cyan' if resonance > 0.99 else 'red', width=2))])
    fig.update_layout(scene=dict(xaxis_title='ΦM', yaxis_title='ΦC', zaxis_title='ΦD'), margin=dict(l=0, r=0, b=0, t=0), template="plotly_dark")
    st.plotly_chart(fig, width='stretch') # Mise à jour conforme aux nouveaux logs
