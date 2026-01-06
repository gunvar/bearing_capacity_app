import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Konfigurasjon av siden
st.set_page_config(page_title="Geoteknisk Bæreevne med Eksentrisitet - EC7", layout="wide")

st.title("🏗️ Bæreevneanalyse for stripefundament")
st.markdown("Basert på Eurokode 7 (NS-EN 1997-1), dimensjonerende kontroll med eksentrisk last.")

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
V_k = st.sidebar.number_input("Vertikallast V (kN/m)", value=350.0, step=10.0)
B = st.sidebar.number_input("Bredde B (m)", value=2.0, min_value=0.1, step=0.1)
D = st.sidebar.number_input("Fundamenteringsdybde D (m)", value=1.0, min_value=0.0, step=0.1)

# Eksentrisitet
st.sidebar.subheader("Eksentrisitet")
e = st.sidebar.slider("Eksentrisitet e (m)", -B/2.01, B/2.01, 0.0, 0.01, 
                      help="Horisontal forskyvning fra fundamentets senterlinje. Begrenset til innenfor fundamentbredden.")

# --- BEREGNINGER med eksentrisitet ---
# Effektiv bredde B' for eksentrisk last
B_prime = B - 2 * abs(e)

# 1. Dimensjonerende friksjon
phi_d_rad = np.arctan(np.tan(np.radians(phi_k)) / gamma_m)
phi_d_deg = np.degrees(phi_d_rad)

# 2. Bæreevnefaktorer (EC7-1 Annex D) basert på phi_d
Nq = np.exp(np.pi * np.tan(phi_d_rad)) * (np.tan(np.radians(45) + phi_d_rad/2))**2
Ngamma = 2 * (Nq - 1) * np.tan(phi_d_rad)

# 3. Effektivt overleiringstrykk ved underkant fundament
q_sur = gamma * D

# 4. Dimensjonerende bæreevne (sigma_d) på effektiv flate B'
# Formel: sigma_d = (q_sur + a)*Nq + 0.5*gamma*B'*Ngamma - a
sigma_d = (q_sur + attraksjon) * Nq + 0.5 * gamma * B_prime * Ngamma - attraksjon

# 5. Faktisk grunntrykk (gjennomsnittlig trykk på effektiv flate)
q_faktisk = V_k / B_prime
utnyttelse = (q_faktisk / sigma_d) * 100

# --- HOVEDPANEL: VISNING ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Grunntrykk (q_fakt)", f"{q_faktisk:.1f} kN/m²")
col2.metric("Bæreevne (σ_d)", f"{sigma_d:.1f} kN/m²")
col3.metric("Effektiv bredde (B')", f"{B_prime:.2f} m")

if utnyttelse <= 100:
    col4.success(f"Utnyttelse: {utnyttelse:.1f}%")
else:
    col4.error(f"Utnyttelse: {utnyttelse:.1f}%")

# --- VISUALISERING (Matplotlib) ---
st.subheader("Fundamentskisse")

fig, ax = plt.subplots(figsize=(10, 5))

# Terrenget
ax.axhline(0, color='brown', lw=2)

# Fundament (rektangel), sentrert rundt x=0
rect = plt.Rectangle((-B/2, -D), B, 0.4, color='grey', alpha=0.8, label="Betongfundament")
ax.add_patch(rect)

# Lastpil - flyttet til posisjon x = e
ax.annotate('', xy=(e, -D + 0.4), xytext=(e, 1.5),
            arrowprops=dict(facecolor='red', shrink=0.05, width=3, headwidth=10))
ax.text(e + 0.1, 1.0, f"V = {V_k:.1f} kN/m", color='red', fontweight='bold')

# Vis eksentrisitet hvis e != 0
if abs(e) > 0.01:
    ax.axvline(0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.plot([0, e], [1.5, 1.5], color='black', marker='|', markersize=5)
    ax.text(e/2, 1.6, f"e={e:.2f}m", color='black', fontsize=9, ha='center')

# --- Dimensjonslinjer B og D ---
dim_offset = 0.3 # Forstyrrelse for dimensjonslinjene

# Dybde D
y_top_d, y_bot_d = 0, -D
x_pos_d = -B/2 - dim_offset
ax.plot([x_pos_d, x_pos_d], [y_top_d, y_bot_d], color='black', marker='_', markersize=8, linewidth=1)
ax.text(x_pos_d - 0.1, (y_top_d + y_bot_d)/2, f"D = {D:.1f} m", 
        color='black', fontsize=10, ha='right', va='center', rotation=90)

# Bredde B
x_left_b, x_right_b = -B/2, B/2
y_pos_b = -D - dim_offset
ax.plot([x_left_b, x_right_b], [y_pos_b, y_pos_b], color='black', marker='|', markersize=8, linewidth=1)
ax.text((x_left_b + x_right_b)/2, y_pos_b - 0.1, f"B = {B:.1f} m", 
        color='black', fontsize=10, ha='center', va='top')


# Akser og styling
ax.set_xlim(-B*2, B*2)
ax.set_ylim(-D-1.5, 3)
ax.set_aspect('equal')
ax.axis('off')
st.pyplot(fig)

# --- TEKNISK OPPSUMMERING ---
with st.expander("Se beregningsdetaljer"):
    st.write(f"**Effektiv fundamentbredde B':** {B_prime:.2f} m")
    st.write(f"**Dimensjonerende tan(φ_d):** {np.tan(phi_d_rad):.3f}")
    st.write(f"**Nq:** {Nq:.2f}")
    st.write(f"**Nγ:** {Ngamma:.2f}")
    st.latex(r"\sigma_d = (q_{sur} + a)N_q + \frac{1}{2}\gamma B' N_\gamma - a")
