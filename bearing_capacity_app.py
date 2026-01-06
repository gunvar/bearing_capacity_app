import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# --- OPPSETT ---
st.set_page_config(page_title="Geoteknisk Bæreevne - Norconsult", layout="wide")
st.title("🏗️ Bæreevneanalyse for stripefundament")
st.markdown("Basert på Eurokode 7 (NS-EN 1997-1) og dimensjonerende kontroll.")

# --- SIDEBAR ---
st.sidebar.header("Inndataparametere")
phi_k = st.sidebar.slider("Friksjonsvinkel (φ_k)", 20.0, 45.0, 32.0, 0.5)
attraksjon = st.sidebar.number_input("Attraksjon (a) [kN/m2]", value=5.0, step=1.0)
gamma = st.sidebar.number_input("Romvekt (γ) [kN/m3]", value=19.0, step=0.5)
gamma_m = st.sidebar.number_input("Materialfaktor (γ_m)", value=1.25, step=0.05)

st.sidebar.markdown("---")
V_k = st.sidebar.number_input("Vertikallast V (kN/m)", value=350.0, step=10.0)
B = st.sidebar.number_input("Bredde B (m)", value=2.0, min_value=0.5, step=0.1)
D = st.sidebar.number_input("Dybde D (m)", value=1.0, min_value=0.0, step=0.1)
e = st.sidebar.slider("Eksentrisitet e (m)", -B/3, B/3, 0.0, 0.01)

# --- BEREGNINGER ---
phi_d_rad = np.arctan(np.tan(np.radians(phi_k)) / gamma_m)
phi_d_deg = np.degrees(phi_d_rad)

# Effektiv bredde og faktorer
B_prime = max(0.1, B - 2 * abs(e))
Nq = np.exp(np.pi * np.tan(phi_d_rad)) * (np.tan(np.radians(45) + phi_d_rad/2))**2
Ngamma = 2 * (Nq - 1) * np.tan(phi_d_rad)

sigma_d = (gamma * D + attraksjon) * np.float64(Nq) + 0.5 * gamma * B_prime * np.float64(Ngamma) - attraksjon
q_faktisk = V_k / B_prime
utnyttelse = (q_faktisk / sigma_d) * 100

# --- HOVEDPANEL: METRIKKER ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Grunntrykk (q)", f"{q_faktisk:.1f} kN/m²")
m2.metric("Bæreevne (σ_d)", f"{sigma_d:.1f} kN/m²")
m3.metric("Utnyttelse", f"{utnyttelse:.1f}%")
m4.metric("B' (effektiv)", f"{B_prime:.2f} m")

# --- FIGURKONSTRUKSJON ---
st.subheader("Fundamentskisse med Bruddfigur")
fig, ax = plt.subplots(figsize=(12, 6))

# Senterlinje og terreng
ax.axhline(0, color='brown', lw=3, zorder=5)
ax.fill_between([-B*3, B*5], -15, 0, color='#fcf3cf', alpha=0.3, zorder=1)

# Finn kantene til det effektive fundamentet
x_center_eff = e 
x_left_eff = x_center_eff - B_prime/2
x_right_eff = x_center_eff + B_prime/2

# Bruddgeometri (Prandtl)
alpha1 = 45 + phi_d_deg/2
alpha2 = 45 - phi_d_deg/2

# Sone 1: Aktiv kile (Trekant under B')
p1 = [x_left_eff, -D]
p2 = [x_right_eff, -D]
h_kile = (B_prime/2) * np.tan(np.radians(alpha1))
p3 = [x_center_eff, -D - h_kile]

# Sone 2 & 3: Spiral og passiv kile (Forenklet for visualisering på høyre side)
r0 = (B_prime/2) / np.cos(np.radians(alpha1))
theta = np.linspace(0, np.pi/2 + np.radians(phi_d_deg), 30)
spiral_pts = []
for t in theta:
    r = r0 * np.exp(t * np.tan(phi_d_rad))
    px = x_right_eff + r * np.cos(np.radians(alpha1) - t)
    py = -D - r * np.sin(np.radians(alpha1) - t)
    spiral_pts.append([px, py])

# Punktet der bruddet når terreng
exit_x = spiral_pts[-1][0] + (abs(spiral_pts[-1][1]) * np.tan(np.radians(45 + phi_d_deg/2)))
pts = [p1, p3] + spiral_pts + [[exit_x, 0], [x_left_eff, 0]]
brudd_poly = Polygon(pts, closed=True, facecolor='orange', alpha=0.3, edgecolor='red', linestyle='--')
ax.add_patch(brudd_poly)

# Fundament (Tegnes over bruddfigur)
rect = plt.Rectangle((-B/2, -D), B, 0.4, color='grey', alpha=1, zorder=10)
ax.add_patch(rect)

# Lastpil
ax.annotate('', xy=(e, -D+0.4), xytext=(e, 2), arrowprops=dict(facecolor='red', width=3))
ax.text(e, 2.2, f"V = {V_k} kN/m", ha='center', color='red', fontweight='bold')

# --- DIMENSJONSLINJER (Robust versjon) ---
# B-linje
ax.plot([-B/2, B/2], [-D - 0.5, -D - 0.5], 'k|-', lw=1.5)
ax.text(0, -D - 0.7, f"B = {B:.1f} m", ha='center', va='top', fontweight='bold')

# D-linje
ax.plot([-B/2 - 0.5, -B/2 - 0.5], [-D, 0], 'k|-', lw=1.5)
ax.text(-B/2 - 0.7, -D/2, f"D = {D:.1f} m", ha='right', va='center', rotation=90, fontweight='bold')

# Akse-styling
ax.set_xlim(-B*1.5, B*3.5)
ax.set_ylim(-D - h_kile - 3, 4)
ax.set_aspect('equal')
ax.axis('off')
st.pyplot(fig)

# --- RESULTATTABELL ---
st.subheader("BELIGGENHET AV KRITISK SKJÆRFLATE:")
c1, c2 = st.columns(2)
with c1:
    dist_kant = exit_x - B/2
    st.write(f"**Avstand fra fundamentkant:** {dist_kant:.1f} m")
    st.write(f"**Dybde under fundamentnivå:** {h_kile:.1f} m")
with c2:
    st.write(f"**Aktiv utgangsvinkel:** {alpha1:.1f} °")
    st.write(f"**Passiv endevinkel:** {alpha2:.1f} °")
