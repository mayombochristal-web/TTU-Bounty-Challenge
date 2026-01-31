import streamlit as st
import numpy as np
import pandas as pd
import hashlib
import secrets
from datetime import datetime

# --- CONFIGURATION THÈME ET PAGE ---
st.set_page_config(
    page_title="TTU-Shield : Quantum Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS pour le look "Cyber-Security"
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #00ff41; }
    .stMetric { background-color: #1a1c24; border: 1px solid #00ff41; padding: 10px; border-radius: 10px; }
    .stTextArea textarea { background-color: #07080a; color: #00ff41; border: 1px solid #00ff41; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTEUR TTU-MC3 ---

class TTUSentinel:
    def __init__(self):
        self.k_viscosity = 0.05
        self.history = [0.05] * 50 
        self.velocity_history = [0.0] * 50 

    def analyze(self, payload):
        if not payload: return 0.0, 0.0, "NORMAL"
        
        # 1. Calcul de l'Entropie (Force du Chaos)
        prob = [float(payload.count(c)) / len(payload) for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        # 2. Vecteur Maître et Vitesse de Phase
        new_k = (0.7 * self.k_viscosity) + (0.3 * (entropy / 8.0))
        dk_dt = new_k - self.k_viscosity
        
        self.k_viscosity = new_k
        self.history.append(new_k)
        self.velocity_history.append(dk_dt)
        
        if len(self.history) > 50:
            self.history.pop(0)
            self.velocity_history.pop(0)
            
        # 3. Niveaux de Menace
        if new_k > 0.75 or dk_dt > 0.18: return new_k, dk_dt, "CRITICAL"
        if new_k > 0.40 or dk_dt > 0.08: return new_k, dk_dt, "WARNING"
        return new_k, dk_dt, "STABLE"

# --- INITIALISATION ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = TTUSentinel()
if 'leaderboard' not in st.session_state:
    st.session_state.leaderboard = []
if 'labyrinth' not in st.session_state:
    st.session_state.labyrinth = False

# --- LOGIQUE D'INTERFACE ---

if not st.session_state.labyrinth:
    # --- MODE DÉFENSE ACTIVE ---
    st.title("🛡️ TTU-Shield : Quantum Sentinel Pro")
    st.subheader("Système de détection par analyse de phase holonome")

    # ÉTAT DES RADARS
    k_curr = st.session_state.sentinel.k_viscosity
    v_curr = st.session_state.sentinel.velocity_history[-1]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("VISCOSITÉ (k)", f"{k_curr:.4f}", delta="Niveau de Dissipation")
    with col2:
        st.metric("RADAR DE PHASE (dk/dt)", f"{v_curr:.4f}", delta="Accélération", delta_color="inverse")
    with col3:
        status_text = "BOUCLIER ACTIF" if k_curr < 0.4 else "INSTABILITÉ"
        st.metric("STATUT SYSTÈME", status_text)

    st.divider()

    c1, c2 = st.columns([1, 1])

    with c1:
        st.header("⌨️ Console d'Attaque")
        alias = st.text_input("Votre Alias Hacker", "Spectre_Alpha")
        payload = st.text_area("Injectez votre Payload (SQL, Code, Chaos...)", height=200)
        
        if st.button("LANCER L'INJECTION"):
            k, dk, lvl = st.session_state.sentinel.analyze(payload)
            
            if lvl == "CRITICAL":
                st.session_state.labyrinth = True
                st.session_state.last_attack = {"alias": alias, "k": k, "dk": dk}
                st.session_state.leaderboard.append({"Hacker": alias, "Force": k, "Vitesse": dk, "Date": datetime.now().strftime("%H:%M")})
                st.rerun()
            elif lvl == "WARNING":
                st.warning(f"⚠️ DÉTECTION : Le Sentinel détecte une anomalie géométrique. (k: {k:.2f})")
            else:
                st.success("✅ ÉCHEC : L'information a été dissipée sans bruit. Le vecteur reste stable.")

    with c2:
        st.header("📊 Monitoring Temps Réel")
        # Graphique de Viscosité (Bleu/Vert Cyber)
        st.write("Amplitude du Vecteur Maître ($k$)")
        st.line_chart(st.session_state.sentinel.history, color="#00ff41")
        
        # Graphique de Vitesse (Rouge Radar)
        st.write("Radar de Phase (Vitesse de Mutation)")
        st.area_chart(st.session_state.sentinel.velocity_history, color="#ff4b4b")

else:
    # --- MODE LABYRINTHE (CONTRE-ATTAQUE) ---
    st.markdown("""<h1 style='text-align: center; color: #ff4b4b;'>🌀 LABYRINTHE DE DISSIPATION ACTIVÉ</h1>""", unsafe_allow_html=True)
    
    att = st.session_state.last_attack
    
    st.error(f"### ALERTE : {att['alias']}, votre signature a été inversée.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"""
        **Analyse de votre défaite :**
        - Votre Force d'impact ($k$) : `{att['k']:.4f}`
        - Votre Accélération ($dk/dt$) : `{att['dk']:.4f}`
        - Résultat : **Capture Holonome**
        """)
    
    with col_b:
        st.write("**Votre empreinte géométrique avant capture :**")
        # Petit graphique "miroir" pour montrer la géométrie inversée
        mirror_data = np.sin(np.linspace(0, 10, 20)) * att['k']
        st.line_chart(mirror_data, color="#ff4b4b")

    st.markdown("---")
    st.markdown("""
    ### 🔓 Comment sortir du Labyrinthe ?
    Votre vecteur est bloqué dans une boucle de rétroaction. Pour libérer vos ressources et retenter le challenge, vous devez reconnaître la supériorité du bouclier TTU.
    
    **Partagez votre capture pour prouver que vous avez osé défier le Sentinel.**
    """)
    
    st.link_button("📢 Partager ma capture sur X / Twitter", 
                   f"https://twitter.com/intent/tweet?text=Mon%20attaque%20a%20été%20dissipée%20par%20le%20TTU-Shield%20!%20Force%20k:%20{att['k']:.2f}.%20Qui%20peut%20faire%20mieux%20?")
    
    if st.button("🔄 Retenter une injection (Reset Phase)"):
        st.session_state.labyrinth = False
        st.session_state.sentinel = TTUSentinel() # Reset du sentinel pour le prochain test
        st.rerun()

# --- FOOTER / LEADERBOARD ---
st.sidebar.title("🏆 Hall of Fail")
if st.session_state.leaderboard:
    df = pd.DataFrame(st.session_state.leaderboard)
    st.sidebar.table(df[["Hacker", "Force"]])
else:
    st.sidebar.write("Aucun hacker capturé pour le moment.")

st.sidebar.divider()
st.sidebar.markdown("""
**Niveaux de difficulté :**
- **0.0 - 0.35** : Drone (Sain)
- **0.36 - 0.70** : Spectre (Suspect)
- **> 0.70** : Anomalie (Bloqué)
""")
