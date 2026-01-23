# cost_params.py — Parámetros de coste por defecto

# Costes por defecto (en unidades monetarias)
DEFAULT_COST_PARAMS = {
    # Costes de disposición de residuos
    "C_disp_heat": 5.0,        # €/MWh - coste de disposición de calor residual
    "C_disp_scrap": 50.0,      # €/t - coste de disposición de scrap plástico
    
    # Costes de insumos vírgenes
    "C_vir_elec": 80.0,        # €/MWh - precio de electricidad virgen
    "C_vir_poly": 1200.0,      # €/t - precio de polímero virgen
    
    # Costes de recuperación/uso (C_lk^use)
    "C_use_heat": 2.0,         # €/MWh - coste de usar calor recuperado
    "C_use_scrap": 20.0,       # €/t - coste de procesar scrap recuperado
    
    # Costes de activación fijos (F_lk)
    "F_fixed_heat": 500.0,     # € - coste fijo de establecer conexión de calor
    "F_fixed_scrap": 800.0,    # € - coste fijo de establecer conexión de scrap
    
    # Costes de transporte
    "T11": 0.5,                # €/(MWh·km) - coste transporte calor
    "T23": 10.0,               # €/(t·km) - coste transporte scrap
}

# Ranges for Streamlit sliders (min, max, step)
COST_RANGES = {
    "C_disp_heat": (1.0, 20.0, 1.0),
    "C_disp_scrap": (10.0, 200.0, 10.0),
    "C_vir_elec": (50.0, 150.0, 5.0),
    "C_vir_poly": (800.0, 2000.0, 100.0),
    "C_use_heat": (0.5, 10.0, 0.5),
    "C_use_scrap": (5.0, 100.0, 5.0),
    "F_fixed_heat": (100.0, 2000.0, 100.0),
    "F_fixed_scrap": (200.0, 3000.0, 100.0),
    "T11": (0.1, 2.0, 0.1),
    "T23": (1.0, 50.0, 1.0),
}

# Descriptions
COST_DESCRIPTIONS = {
    "C_disp_heat": "Waste heat disposal cost (€/MWh)",
    "C_disp_scrap": "Plastic scrap disposal cost (€/t)",
    "C_vir_elec": "Virgin electricity cost (€/MWh)",
    "C_vir_poly": "Virgin polymer cost (€/t)",
    "C_use_heat": "Heat recovery/use cost (€/MWh)",
    "C_use_scrap": "Scrap processing/use cost (€/t)",
    "F_fixed_heat": "Fixed activation cost - heat connection (€)",
    "F_fixed_scrap": "Fixed activation cost - scrap connection (€)",
    "T11": "Heat transport cost (€/MWh·km)",
    "T23": "Scrap transport cost (€/t·km)",
}
