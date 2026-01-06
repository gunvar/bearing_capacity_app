import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Konfigurasjon av siden
st.set_page_config(page_title="Geoteknisk Bæreevne - EC7", layout="wide")

st.title("🏗️ Bæreevneanalyse for stripefundament")
st.markdown("Basert på Eurokode 7 (NS-EN 1997-1) og dimensjonerende kontroll.")

# --- SIDEBAR: INPUT ---
st.sidebar.header("Inndataparametere")

# Materialparametere
st.sidebar.subheader("Jordparametere")
phi_k = st.sidebar.slider("Karakteristisk friksjonsvinkel (φ_k)", 20.0, 45.0, 32.0, 0.5)
attraksjon = st.sidebar.number_input("Attraksjon (a) [kN/m2]", value=5.0, step=1.0)
gamma = st.sidebar.number_input("Romvekt (γ) [kN/m3]", value=19.0, step=0.5)
gamma_m = st.sidebar.number_input("Materialfaktor (γ_m)", value=1.25, step=0.05)

# Geometri og last
st.sidebar.subheader("Geometri og Last")
V_k = st.sidebar.number_input("Vertikallast V (kN/m)", value=250.0, step=10.0)
B = st.sidebar.number_input("Bredde B (m)", value=2.0, min_value=0.1, step=0.1)
D = st.sidebar.number_input("Fundamenteringsdybde D (m)", value=1.0, min_value=0.0, step=0.1)

# --- BEREGNINGER ---
# 1. Dimensjonerende friksjon
phi_d_rad = np.arctan(np.tan(np.radians(phi_k)) / gamma_m)
phi_d_deg = np.degrees(phi_d_rad)

# 2. Bæreevnefaktorer (EC7-1 Annex D)
Nq = np.exp(np.pi * np.tan(phi_d_rad)) * (np.tan(np.radians(45) + phi_d_rad/2))**2
Ngamma = 2 * (Nq - 1) * np.tan(phi_d_rad)

# 3. Effektivt overleiringstrykk
q_sur = gamma * D

# 4. Dimensjonerende bæreevne (sigma_d)
# Formel: sigma_d = (q_sur + a)*Nq + 0.5*gamma*B*Ngamma - a
sigma_d = (q_sur + attraksjon) * Nq + 0.5 * gamma * B * Ngamma - attraksjon

# 5. Faktisk grunntrykk
q_faktisk = V_k / B
utnyttelse = (q_faktisk / sigma_d) * 100

# --- HOVEDPANEL: VISNING ---
col1, col2, col3 = st.columns(3)
col1.metric("Grunntrykk (q)", f"{q_faktisk:.1f} kN/m²")
col2.metric("Bæreevne (σ_d)", f"{sigma_d:.1f} kN/m²")

if utnyttelse <= 100:
    col3.success(f"Utnyttelse: {utnyttelse:.1f}%")
else:
    col3.error(f"Utnyttelse: {utnyttelse:.1f}%")

# --- VISUALISERING (Matplotlib) ---
st.subheader("Fundamentskisse")

fig, ax = plt.subplots(figsize=(8, 4))

# Terrenget
ax.axhline(0, color='brown', lw=2, label="Terreng")

# Fundament (rektangel)
# x = center - B/2, y = -D
rect = plt.Rectangle((-B/2, -D), B, 0.4, color='grey', alpha=0.8, label="Betongfundament")
ax.add_patch(rect)

# Lastpil
ax.annotate('', xy=(0, -D + 0.4), xytext=(0, 1),
            arrowprops=dict(facecolor='red', shrink=0.05, width=3))
ax.text(0.2, 0.5, f"V = {V_k} kN/m", color='red', fontweight='bold')

# Akser og styling
ax.set_xlim(-B*2, B*2)
ax.set_ylim(-D-1, 2)
ax.set_aspect('equal')
ax.axis('off')
st.pyplot(fig)

# --- TEKNISK OPPSUMMERING ---
with st.expander("Se beregningsdetaljer"):
    st.write(f"**Dimensjonerende tan(φ_d):** {np.tan(phi_d_rad):.3f}")
    st.write(f"**Nq:** {Nq:.2f}")
    st.write(f"**Nγ:** {Ngamma:.2f}")
    st.latex(r"\sigma_d = (q_{sur} + a)N_q + \frac{1}{2}\gamma B N_\gamma - a")
