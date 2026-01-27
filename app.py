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
# [span_4](start_span)[span_5](start_span)Basé sur le Lagrangien L_MC3 et la fonction dissipative R[span_4](end_span)[span_5](end_span)
def ttu_system(t, y, phi_c_input):
    pm, pc, pd = y
    # [span_6](start_span)[span_7](start_span)Paramètres de potentiel assurant les bifurcations[span_6](end_span)[span_7](end_span)
    a, b = -1.0, 1.0
    lambda_mcd = 1.2
    [span_8](start_span)eta_d = 0.8 # Coefficient de dissipation[span_8](end_span)
    
    # [span_9](start_span)Équations d'évolution Triadique (Page 14 du document)[span_9](end_span)
    dpm = -(2*a*pm + 4*b*pm**3) + lambda_mcd * pc * pd
    dpc = -(2*(-0.5)*pc + 4*0.8*pc**3) + lambda_mcd * pm * pd
    
    # La déviance de phase injectée par l'utilisateur perturbe la dissipation
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
    CLÉ DE PHASE (ΦC) : {phase}
    RÉGIME : COHÉRENCE QUANTIQUE DOMINANTE
    COURBURE K : {K_CURVATURE}
    
    Signature de l'Attracteur : STABLE - MC3-Verified
    ----------------------------------
    """
    b64 = base64.b64encode(cert_text.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="TTU_Certificate.txt">📥 Télécharger votre Certificat de Résonance</a>'

# --- INTERFACE UTILISATEUR ---
st.title("🌌 TTU MC³ : Dashboard de Phase Event Horizon")
st.markdown(f"**Analyseur de Flot Triadique - Basé sur les paramètres CERN K = {K_CURVATURE}**")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Console de Contrôle")
    phi_c_user = st.number_input("Entrer la Clé de Phase (ΦC)", value=0.000000, format="%.6f", help="La clé doit être précise à 10⁻⁶ pour annuler la courbure K.")
    
    # [span_10](start_span)Calcul de la résonance (marge d'erreur minime pour l'inviolabilité[span_10](end_span))
    resonance = 1.0 - min(abs(phi_c_user - PHI_C_REF) * 100, 1.0)
    
    st.metric("Indice de Résonance", f"{resonance*100:.4f}%")
    
    if resonance > 0.9999:
        st.success("✅ ÉTAT : RÉSONANCE - Flux Déchiffré")
        st.write("**Message Cible :** 'Le temps est un flux irréversible.'")
        # Affichage du bouton de téléchargement du certificat
        st.markdown(generate_certificate(phi_c_user), unsafe_allow_html=True)
    else:
        st.error("❌ ÉTAT : DÉCOHÉRENCE - Bruit Hyperbolique")
        st.warning("La courbure négative expulse la trajectoire de l'attracteur stable.")

with col2:
    # [span_11](start_span)[span_12](start_span)Simulation du système dynamique[span_11](end_span)[span_12](end_span)
    y0 = [0.2, 0.1, 0.3]
    t_eval = np.linspace(0, 100, 5000)
    sol = solve_ivp(ttu_system, (0, 100), y0, t_eval=t_eval, args=(phi_c_user,))
    
    # [span_13](start_span)Tracé de l'attracteur 3D (Espace des phases : Mémoire, Cohérence, Dissipation)[span_13](end_span)
    fig = go.Figure(data=[go.Scatter3d(
        x=sol.y[0], y=sol.y[1], z=sol.y[2],
        mode='lines',
        line=dict(color='cyan' if resonance > 0.99 else 'red', width=2),
        name="Trajectoire MC³"
    )])
    
    fig.update_layout(
        title="Visualisation de l'Attracteur (Matière Émergente)",
        scene=dict(
            xaxis_title='ΦM (Mémoire)',
            yaxis_title='ΦC (Cohérence)',
            zaxis_title='ΦD (Dissipation)'
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()
[span_14](start_span)st.info("Note : La masse effective de cet attracteur est proportionnelle à sa profondeur dissipative (ΦD²).[span_14](end_span)")


