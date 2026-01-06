import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# --- KONFIGURASJON ---
st.set_page_config(page_title="Geoteknikk: Bæreevne (EC7)", layout="wide")

st.title("🏗️ Bæreevneanalyse for stripefundament")
st.markdown("Dimensjonerende kontroll i henhold til Eurokode 7 (NS-EN 1997-1).")

# --- SIDEBAR: INPUT ---
st.sidebar.header("Inndataparametere")

st.sidebar.subheader("Jordparametere")
phi_k = st.sidebar.slider("Friksjonsvinkel (φ_k) [grader]", 20.0, 45.0, 32.0, 0.5)
attraksjon = st.sidebar.number_input("Attraksjon (a) [kN/m2]", value=5.0, step=1.0)
gamma = st.sidebar.number_input("Romvekt (γ) [kN/m3]", value=19.0, step=0.5)
gamma_m = st.sidebar.number_input("Materialfaktor (γ_m)", value=1.25, step=0.05)

st.sidebar.subheader("Geometri og Last")
V_k = st.sidebar.number_input("Vertikallast V [kN/m]", value=350.0, step=10.0)
B = st.sidebar.number_input("Bredde B [m]", value=2.0, min_value=0.5, step=0.1)
D = st.sidebar.number_input("Dybde D [m]", value=1.0, min_value=0.0, step=0.1)
e = st.sidebar.slider("Eksentrisitet e [m]", -B/3, B/3, 0.0, 0.01)

# --- BEREGNINGER ---
# 1. Dimensjonerende verdier
phi_d_rad = np.arctan(np.tan(np.radians(phi_k)) / gamma_m)
phi_d_deg = np.degrees(phi_d_rad)

# 2. Effektiv bredde
B_prime = B - 2 * abs(e)

# 3. Bæreevnefaktorer (EC7-1 Annex D)
Nq = np.exp(np.pi * np.tan(phi_d_rad)) * (np.tan(np.radians(45) + phi_d_rad/2))**2
Ngamma = 2 * (Nq - 1) * np.tan(phi_d_rad)

# 4. Kapasitet og grunntrykk
q_sur = gamma * D
sigma_d = (q_sur + attraksjon) * Nq + 0.5 * gamma * B_prime * Ngamma - attraksjon
q_faktisk = V_k / B_prime
utnyttelse = (q_faktisk / sigma_d) * 100

# --- HOVEDPANEL: METRICS ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Grunntrykk (q)", f"{q_faktisk:.1f} kN/m²")
m2.metric("Bæreevne (σ_d)", f"{sigma_d:.1f} kN/m²")
m3.metric("Utnyttelse", f"{utnyttelse:.1f}%")
m4.metric("B' (effektiv)", f"{B_prime:.2f} m")

# --- GEOMETRI FOR BRUDDFIGUR ---
# Definerer koordinater for skjærflaten (Prandtl)
# Symmetri: Vi tegner bruddet ut til høyre hvis e >= 0, ellers venstre.
side = 1 if e >= 0 else -1
x_eff_start = e - (side * B_prime/2)
x_eff_end = e + (side * B_prime/2)
y_base = -D

# Punkt 1: Indre kant av effektivt fundament
p1 = [x_eff_start, y_base]

# Punkt 2: Aktiv kile (spiss under senter av B')
alpha1_rad = np.radians(45 + phi_d_deg/2)
h_kile = (B_prime/2) * np.tan(alpha1_rad)
p_apex = [e, y_base - h_kile]

# Sone 2: Logaritmisk spiral
r0 = (B_prime/2) / np.cos(alpha1_rad)
theta_vals = np.linspace(0, np.pi/2 + np.radians(phi_d_deg), 25)
spiral_pts = []
for t in theta_vals:
    r = r0 * np.exp(t * np.tan(phi_d_rad))
    # Vinkel i forhold til horisontalen
    angle = alpha1_rad - t
    px = x_eff_end + (side * r * np.cos(angle))
    py = y_base - (r * np.sin(angle))
    spiral_pts.append([px, py])

# Punkt 3: Utgang terreng (Passiv kile)
# Vi antar at bruddet følger en rett linje fra spiralens slutt til terrengoverflaten (y=0)
p_last_spiral = spiral_pts[-1]
# Vinkel for passiv kile mot horisontalen: 45 - phi/2
exit_angle = np.radians(45 - phi_d_deg/2)
# Horisontal avstand fra spiral-slutt til terreng: x = dybde / tan(vinkel)
dx_exit = abs(p_last_spiral[1]) * np.tan(np.radians(90) - exit_angle)
p_exit = [p_last_spiral[0] + (side * dx_exit), 0]

# Sett sammen polygon (lukket flate)
poly_pts = [p1, p_apex] + spiral_pts + [p_exit, [x_eff_start, 0]]

# --- FIGUR ---
st.subheader("Fundamentskisse med Bruddfigur")
fig, ax = plt.subplots(figsize=(10, 5))

# Terreng og jordfyll
ax.fill_between([-B*2, B*4], -10, 0, color='#fdf2e9', zorder=0)
ax.axhline(0, color='brown', lw=3, zorder=5)

# Tegn bruddfiguren
failure_poly = Polygon(poly_pts, closed=True, facecolor='orange', alpha=0.3, 
                       edgecolor='red', linestyle='--', linewidth=1.5, label="Kritisk skjærflate")
ax.add_patch(failure_poly)

# Tegn fundamentet
rect = plt.Rectangle((-B/2, -D), B, 0.4, color='grey', alpha=1, zorder=10)
ax.add_patch(rect)

# Lastpil
ax.annotate('', xy=(e, -D+0.4), xytext=(e, 2.0), 
            arrowprops=dict(facecolor='red', width=3, headwidth=10))
ax.text(e, 2.2, f"V = {V_k:.1f} kN/m", color='red', weight='bold', ha='center')

# --- Dimensjonslinjer (Presise etiketter) ---
# B-linje (Horisontal under fundament)
ax.plot([-B/2, B/2], [y_base - 0.5, y_base - 0.5], 'k|-', lw=1)
ax.text(0, y_base - 0.7, f"B = {B:.1f} m", ha='center', va='top')

# D-linje (Vertikal fra terreng til base)
# Bruker abs() og f-string for å unngå vitenskapelig notasjon ved D=0
ax.plot([-B/2 - 0.3, -B/2 - 0.3], [y_base, 0], 'k|-', lw=1)
ax.text(-B/2 - 0.5, y_base/2 if D > 0 else -0.2, f"D = {D:.1f} m", 
        ha='right', va='center', rotation=90)

# Styling
ax.set_aspect('equal')
ax.set_xlim(-B*1.5, B*3.5)
ax.set_ylim(-D - h_kile - 3, 4)
ax.axis('off')
st.pyplot(fig)

# --- RESULTATTABELL OG FORMLER ---
st.subheader("BELIGGENHET AV KRITISK SKJÆRFLATE:")
c1, c2 = st.columns(2)

dist_kant = abs(p_exit[0] - (side * B/2))
with c1:
    st.write(f"**Avstand fra fundamentkant:** {dist_kant:.1f} m")
    st.write(f"**Dybde under fundamentnivå:** {h_kile:.1f} m")

with c2:
    st.write(f"**Aktiv utgangsvinkel (α₁):** {(45 + phi_d_deg/2):.1f} °")
    st.write(f"**Passiv endevinkel (α₂):** {(45 - phi_d_deg/2):.1f} °")

# --- FORMLER (Som i første versjon) ---
with st.expander("Beregninger og Formler (Eurokode 7)"):
    st.markdown("### Dimensjonerende verdier")
    st.latex(r"\tan \phi_d = \frac{\tan \phi_k}{\gamma_m}")
    st.latex(r"B' = B - 2|e|")
    
    st.markdown("### Bæreevnefaktorer")
    st.latex(r"N_q = e^{\pi \tan \phi_d} \cdot \tan^2(45 + \phi_d/2)")
    st.latex(r"N_\gamma = 2(N_q - 1) \tan \phi_d")
    
    st.markdown("### Dimensjonerende bæreevne")
    st.latex(r"\sigma_d = (q_{sur} + attraksjon) \cdot N_q + \frac{1}{2} \gamma B' N_\gamma - attraksjon")
    st.info(f"Her er q_sur = γ · D = {gamma * D:.1f} kN/m²")
