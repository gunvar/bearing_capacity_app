import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# Konfigurasjon
st.set_page_config(page_title="Geoteknisk Bæreevne & Bruddfigur", layout="wide")

st.title("🏗️ Bæreevneanalyse med Bruddfigur")
st.markdown("Beregning av bæreevne og visualisering av kritisk skjærflate iht. EC7.")

# --- SIDEBAR: INPUT ---
st.sidebar.header("Inndataparametere")

# Jordparametere
st.sidebar.subheader("Jordparametere")
phi_k = st.sidebar.slider("Karakteristisk friksjonsvinkel (φ_k)", 20.0, 45.0, 32.0, 0.5)
attraksjon = st.sidebar.number_input("Attraksjon (a) [kN/m2]", value=5.0, step=1.0)
gamma = st.sidebar.number_input("Romvekt (γ) [kN/m3]", value=19.0, step=0.5)
gamma_m = st.sidebar.number_input("Materialfaktor (γ_m)", value=1.25, step=0.05)

# Geometri og last
st.sidebar.subheader("Geometri og Last")
V_k = st.sidebar.number_input("Vertikallast V (kN/m)", value=350.0, step=10.0)
B = st.sidebar.number_input("Bredde B (m)", value=2.0, min_value=0.5, step=0.1)
D = st.sidebar.number_input("Dybde D (m)", value=1.0, min_value=0.0, step=0.1)

# Eksentrisitet
e = st.sidebar.slider("Eksentrisitet e (m)", -B/3, B/3, 0.0, 0.01)

# --- BEREGNINGER ---
phi_d_rad = np.arctan(np.tan(np.radians(phi_k)) / gamma_m)
phi_d_deg = np.degrees(phi_d_rad)

# Effektiv bredde
B_prime = B - 2 * abs(e)

# Bæreevnefaktorer
Nq = np.exp(np.pi * np.tan(phi_d_rad)) * (np.tan(np.radians(45) + phi_d_rad/2))**2
Ngamma = 2 * (Nq - 1) * np.tan(phi_d_rad)

sigma_d = (gamma * D + attraksjon) * Nq + 0.5 * gamma * B_prime * Ngamma - attraksjon
q_faktisk = V_k / B_prime
utnyttelse = (q_faktisk / sigma_d) * 100

# --- GEOMETRI FOR SKJÆRFLATE (Prandtl) ---
# Vinkler
alpha_1 = 45 + phi_d_deg/2  # Aktiv utgangsvinkel
alpha_2 = 45 - phi_d_deg/2  # Passiv endevinkel

# Startpunkt for bruddfigur (venstre eller høyre side av B')
side = 1 if e >= 0 else -1
x_start = e - (side * B_prime/2)
x_end_base = e + (side * B_prime/2)

# Koordinater for Sone 1 (Aktiv kile)
p1 = [x_start, -D]
p2 = [x_end_base, -D]
p3 = [x_start + (side * B_prime * np.cos(np.radians(alpha_1)) * np.cos(np.radians(phi_d_deg)) / np.sin(np.radians(90+phi_d_deg))), 
      -D - (B_prime * np.sin(np.radians(alpha_1)) * np.cos(np.radians(phi_d_deg)) / np.sin(np.radians(90+phi_d_deg)))]

# Sone 2 (Logaritmisk spiral) og Sone 3 (Passiv kile)
# Forenklet beregning for visualisering av influensområde
theta = np.linspace(0, np.pi/2 + np.radians(phi_d_deg), 20)
r0 = B_prime / (2 * np.cos(np.radians(alpha_1)))
spiral_pts = []
for t in theta:
    r = r0 * np.exp(t * np.tan(phi_d_rad))
    px = x_end_base + (side * r * np.cos(np.radians(alpha_1) - t))
    py = -D - (r * np.sin(np.radians(alpha_1) - t))
    spiral_pts.append([px, py])

# Finn ytterpunktet på terreng
exit_x = x_end_base + side * (B_prime * np.exp((np.pi/2) * np.tan(phi_d_rad)) * np.tan(np.radians(45 + phi_d_deg/2)))
dist_fra_kant = abs(exit_x - (side * B/2))
max_dybde = abs(min([p[1] for p in spiral_pts])) - D

# --- VISNING ---
col1, col2, col3 = st.columns(3)
col1.metric("Bæreevne (σ_d)", f"{sigma_d:.1f} kN/m²")
col2.metric("Utnyttelse", f"{utnyttelse:.1f}%")
col3.metric("B' (effektiv)", f"{B_prime:.2f} m")

# FIGUR
st.subheader("Fundamentskisse med Bruddfigur")
fig, ax = plt.subplots(figsize=(12, 6))

# Jord / Terreng
ax.fill_between([-B*3, B*5], -10, 0, color='#f4ead5', zorder=1)
ax.axhline(0, color='brown', lw=3, zorder=5)

# Bruddfigur (Skjærflate)
pts = [p1, p3] + spiral_pts + [[exit_x, 0], [x_start, 0]]
failure_zone = Polygon(pts, closed=True, facecolor='orange', alpha=0.3, edgecolor='red', linestyle='--', label="Kritisk skjærflate")
ax.add_patch(failure_zone)

# Fundament
foundation = plt.Rectangle((-B/2, -D), B, 0.4, color='grey', alpha=0.9, zorder=10, label="Fundament")
ax.add_patch(foundation)

# Lastpil (Eksentrisk)
ax.annotate('', xy=(e, -D+0.4), xytext=(e, 2), arrowprops=dict(facecolor='red', width=4))
ax.text(e, 2.2, f"V={V_k} kN/m", ha='center', color='red', weight='bold')

# Dimensjonslinjer
ax.plot([-B/2, B/2], [-D-0.5, -D-0.5], 'k|-') # B
ax.text(0, -D-0.8, f"B = {B}m", ha='center')
ax.plot([-B/2-0.5, -B/2-0.5], [-D, 0], 'k|-') # D
ax.text(-B/2-0.7, -D/2, f"D = {D}m", va='center', rotation=90)

# Styling
ax.set_xlim(-B*2, B*4 if e>=0 else B*2)
ax.set_ylim(-D - max_dybde - 1, 3)
ax.set_aspect('equal')
ax.axis('off')
st.pyplot(fig)

# --- RESULTATTABELL (Slik bildet ditt viste) ---
st.subheader("BELIGGENHET AV KRITISK SKJÆRFLATE:")
res_col1, res_col2 = st.columns(2)

with res_col1:
    st.write(f"**Avstand fra fundamentkant:** {dist_fra_kant:.2f} m")
    st.write(f"**Dybde under fundamentnivå:** {max_dybde:.2f} m")

with res_col2:
    st.write(f"**Aktiv utgangsvinkel:** {alpha_1:.1f} °")
    st.write(f"**Passiv endevinkel:** {alpha_2:.1f} °")

with st.expander("Tekniske detaljer & Formler"):
    st.latex(r"B' = B - 2e")
    st.latex(r"N_q = e^{\pi \tan \phi_d} \tan^2(45 + \phi_d/2)")
    st.write("Skjærflaten er beregnet som en kombinasjon av Rankine-kiler og en logaritmisk spiral (Prandtl-mekanismen).")
