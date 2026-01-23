# ======================================================
# Step 1a: General EIO baseline with Z0 (Álava Technology Park) (Datos estimados)
# ======================================================

import numpy as np
import pandas as pd
from numpy.linalg import eigvals
import pulp as pl
from math import radians, sin, cos, sqrt, atan2

# ------------------------------------------------------
# 1. Definición de datos: sectores, inputs, wastes
# ------------------------------------------------------

sectors_short = ["F1", "F2", "F3", "F4", "F5"]
sectors_long = [
    "F1_Electronics",
    "F2_MetalProcessing",
    "F3_Composites",
    "F4_Packaging",
    "F5_Services"
]

inputs = ["Electricity", "Water", "Virgin polymer"]
wastes = ["Waste heat", "Plastic scrap"]

# ------------------------------------------------------
# 2. Matrices y vectores de BASELINE
#    (puedes cambiar Z0 más adelante y todo se recalcula)
# ------------------------------------------------------

# 2.1 Intermediate deliveries Z0 (en unidades físicas por año)
# Baseline: no hay entregas intermedias -> Z0 = 0
Z0 = np.zeros((5, 5), dtype=float)

# EJEMPLO (si quisieras introducir inter-firm flows en el futuro):
# Z0 = np.array([
#     [0.0, 0.5, 0.0, 0.0, 0.0],
#     [0.0, 0.0, 0.3, 0.0, 0.0],
#     [0.0, 0.0, 0.0, 0.4, 0.0],
#     [0.0, 0.0, 0.0, 0.0, 0.2],
#     [0.1, 0.0, 0.0, 0.0, 0.0]
# ])

# 2.2 Final demand vector Y (tu tabla de baseline)
Y = np.array([10.0, 8.0, 6.0, 5.0, 4.0], dtype=float)

# 2.3 Primary input intensities R0 (Tabla R0)
R0 = np.array([
    # F1    F2    F3    F4    F5
    [0.40, 0.20, 0.10, 0.20, 0.20],  # Electricity (MWh per unit)
    [0.00, 0.20, 0.10, 0.00, 0.00],  # Water (m3 per unit)
    [0.00, 0.10, 0.40, 0.00, 0.00]   # Virgin polymer (t per unit)
], dtype=float)

# 2.4 Waste intensities W0 (Tabla W0)
W0 = np.array([
    # F1    F2    F3    F4    F5
    [0.10, 0.20, 0.00, 0.00, 0.00],  # Waste heat
    [0.00, 0.00, 0.20, 0.00, 0.10]   # Scrap
], dtype=float)

# 2.5 Emission intensities f0 (tCO2 por unidad de output)
f0 = np.array([0.50, 0.40, 0.60, 0.30, 0.50], dtype=float)

# ------------------------------------------------------
# 3. Cálculo del equilibrio: x, A0, recursos, residuos, emisiones
# ------------------------------------------------------

# 3.1 Gross output x a partir de Z0 y Y
# Identidad en filas: x_i = sum_j Z_ij + Y_i
x = Z0.sum(axis=1) + Y   # vector (5,)

# 3.2 Construir matriz de coeficientes técnicos A0 a partir de Z0 y x
# Convención IO típica: A_ij = Z_ij / x_j (column-wise)
A0 = np.zeros_like(Z0, dtype=float)
for j in range(len(x)):
    if x[j] > 0:
        A0[:, j] = Z0[:, j] / x[j]
    else:
        A0[:, j] = 0.0

# 3.3 Comprobar estabilidad (es opcional, pero lo mantenemos)
rho = max(abs(eigvals(A0)))
print(f"\nSpectral radius ρ(A0) = {rho:.3f}")

# 3.4 Recursos, residuos y emisiones
r = R0 @ x          # total primary inputs (3,)
w = W0 @ x          # total wastes (2,)
E = f0 * x          # emisiones por firma

# ------------------------------------------------------
# 4. Tablas por firmas y totales
# ------------------------------------------------------

# 4.1 Tabla x vs Y (para ver explícitamente que x puede ser distinto de Y si Z0 ≠ 0)
df_xY = pd.DataFrame({
    "Sector": sectors_long,
    "x (gross output)": x,
    "Y (final demand)": Y
})

# 4.2 Intensidades R0 y W0 por firma
df_R0 = pd.DataFrame(R0, index=inputs, columns=sectors_short)
df_W0 = pd.DataFrame(W0, index=wastes, columns=sectors_short)

# 4.3 Totales de recursos R0 * x
df_R_totals = pd.DataFrame({
    "Primary input": inputs,
    "Total": r,
    "Units": ["MWh", "m³", "t"]
})

# 4.4 Totales de residuos W0 * x
df_W_totals = pd.DataFrame({
    "Waste type": wastes,
    "Total": w,
    "Units": ["MWh", "t"]
})

# 4.5 Tabla de emisiones por firma + total
df_emissions = pd.DataFrame({
    "Sector": sectors_long,
    "Output (x_i)": x,
    "CO2 intensity (tCO2/unit)": f0,
    "Emissions (tCO2)": E
})

total_row = pd.DataFrame({
    "Sector": ["Total"],
    "Output (x_i)": [x.sum()],
    "CO2 intensity (tCO2/unit)": [E.sum() / x.sum()],
    "Emissions (tCO2)": [E.sum()]
})

df_emissions_full = pd.concat([df_emissions, total_row], ignore_index=True)

# ------------------------------------------------------
# 5. Prints de resumen (para comprobar)
# ------------------------------------------------------

print("\n=== x vs Y (equilibrium with Z0 and Y) ===")
print(df_xY.round(3).to_string(index=False))

print("\n=== Primary Input Intensities R0 (per firm) ===")
print(df_R0.round(3).to_string())

print("\n=== Waste Intensities W0 (per firm) ===")
print(df_W0.round(3).to_string())

print("\n=== Total Primary Resource Use R0 * x ===")
print(df_R_totals.round(3).to_string(index=False))

print("\n=== Total Waste Generation W0 * x ===")
print(df_W_totals.round(3).to_string(index=False))

print("\n=== Emissions per firm and total ===")
print(df_emissions_full.round(3).to_string(index=False))

print("\nTotal output Σx =", x.sum())
print("Total emissions ΣE =", E.sum())

# ------------------------------------------------------
# 6. Guardar baseline para usar luego en el MILP
# ------------------------------------------------------

baseline = {
    "Z0": Z0,
    "A0": A0,
    "Y": Y,
    "x": x,
    "R0": R0,
    "W0": W0,
    "f0": f0,
    "r": r,
    "w": w,
    "E": E
}

# ======================================================
# NEW (for GIS MILP Option 2): firm-level supplies/demands
# ======================================================

# Firm-level waste supply S_il (shape: n_firms x n_wastes)
# W0 is (n_wastes x n_firms), so transpose and multiply by x (per firm)
S_il_eoi = (W0.T * x[:, None])   # (5 x 2) columns: [Waste heat, Plastic scrap]

# Firm-level input demand D_jk (shape: n_firms x n_inputs)
# R0 is (n_inputs x n_firms), so transpose and multiply by x
D_jk_eoi = (R0.T * x[:, None])   # (5 x 3) columns: [Electricity, Water, Virgin polymer]

# Optional: make DataFrames for readability
df_S_il_eoi = pd.DataFrame(S_il_eoi, index=sectors_short, columns=wastes)
df_D_jk_eoi = pd.DataFrame(D_jk_eoi, index=sectors_short, columns=inputs)

print("\n=== Firm-level Waste Supply S_il (EOI estimate) ===")
print(df_S_il_eoi.round(3).to_string())

print("\n=== Firm-level Input Demand D_jk (EOI estimate) ===")
print(df_D_jk_eoi.round(3).to_string())

# Store into baseline dict for later MILP use
baseline["S_il_eoi"] = S_il_eoi
baseline["D_jk_eoi"] = D_jk_eoi

