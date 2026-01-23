# optimizer.py
# --------------------------------------------------
# Optimización MILP para Simbiosis Industrial (GIS)
# Calor residual -> Electricidad
# Scrap plástico -> Polímero virgen
# --------------------------------------------------

import numpy as np
import pandas as pd
import pulp as pl


def solve_milp(
    S_il: pd.DataFrame,
    D_jk: pd.DataFrame,
    dist_ij: np.ndarray,
    cost_params: dict,
    r11: float = 0.9,
    r23: float = 0.8,
    synergy_matrix=None,
    delta_heat_elec: float = 1.0,
    delta_scrap_poly: float = 1.0,
    delta_steam_water: float = 1.0,
):
    """
    Resuelve el MILP para un escenario.

    Parámetros
    ----------
    S_il : DataFrame (n_firms x 2)
        Oferta de residuos [Waste heat, Plastic scrap]
    D_jk : DataFrame (n_firms x 3)
        Demanda de inputs [Electricity, Water, Virgin polymer]
    dist_ij : ndarray (n_firms x n_firms)
        Distancias entre firmas
    cost_params : dict
        Parámetros de coste:
        {
            "C_disp_heat": float,
            "C_disp_scrap": float,
            "C_vir_elec": float,
            "C_vir_poly": float,
            "T11": float,
            "T23": float
        }
    r11 : float
        Eficiencia calor -> electricidad
    r23 : float
        Eficiencia scrap -> polímero
    delta_heat_elec : float
        Máxima tasa de sustitución (0-1) para electricidad desde calor
    delta_scrap_poly : float
        Máxima tasa de sustitución (0-1) para polímero desde scrap
    delta_steam_water : float
        Máxima tasa de sustitución (0-1) para agua desde vapor
    """

    firms = S_il.index.tolist()
    n = len(firms)
    
    # --------------------------------------------------
    # Detect enabled synergies from synergy_matrix
    # --------------------------------------------------
    if synergy_matrix is not None and hasattr(synergy_matrix, 'loc'):
        # Check which synergies are enabled
        heat_to_elec_enabled = synergy_matrix.loc["Waste heat", "Electricity"]
        scrap_to_poly_enabled = synergy_matrix.loc["Plastic scrap", "Polymer"]
        steam_to_water_enabled = synergy_matrix.loc["Steam/Wastewater", "Water"]
    else:
        # Default: enable heat and scrap, disable steam (backward compatibility)
        heat_to_elec_enabled = True
        scrap_to_poly_enabled = True
        steam_to_water_enabled = False

    # --------------------------------------------------
    # Modelo
    # --------------------------------------------------
    model = pl.LpProblem("Industrial_Symbiosis", pl.LpMinimize)

    # --------------------------------------------------
    # Variables
    # --------------------------------------------------
    q11 = pl.LpVariable.dicts(
        "q_heat_to_elec",
        ((i, j) for i in range(n) for j in range(n) if i != j),
        lowBound=0,
    )

    q23 = pl.LpVariable.dicts(
        "q_scrap_to_poly",
        ((i, j) for i in range(n) for j in range(n) if i != j),
        lowBound=0,
    )

    z11 = pl.LpVariable.dicts(
        "z_heat_to_elec",
        ((i, j) for i in range(n) for j in range(n) if i != j),
        cat="Binary",
    )

    z23 = pl.LpVariable.dicts(
        "z_scrap_to_poly",
        ((i, j) for i in range(n) for j in range(n) if i != j),
        cat="Binary",
    )

    # --------------------------------------------------
    # Restricciones
    # --------------------------------------------------

    # Oferta de residuos (solo para sinergias habilitadas)
    for i in range(n):
        if heat_to_elec_enabled:
            model += pl.lpSum(q11[i, j] for j in range(n) if i != j) <= S_il.iloc[i, 0]
        else:
            # Si no está habilitada, forzar q11 = 0
            for j in range(n):
                if i != j:
                    model += q11[i, j] == 0
        
        if scrap_to_poly_enabled:
            model += pl.lpSum(q23[i, j] for j in range(n) if i != j) <= S_il.iloc[i, 1]
        else:
            # Si no está habilitada, forzar q23 = 0
            for j in range(n):
                if i != j:
                    model += q23[i, j] == 0

    # Demanda (sustitución de insumos vírgenes) - solo para sinergias habilitadas
    for j in range(n):
        if heat_to_elec_enabled:
            model += r11 * pl.lpSum(q11[i, j] for i in range(n) if i != j) <= D_jk.iloc[j, 0]
        if scrap_to_poly_enabled:
            model += r23 * pl.lpSum(q23[i, j] for i in range(n) if i != j) <= D_jk.iloc[j, 2]
    
    # --------------------------------------------------
    # Restricciones de Substitución Máxima (δ)
    # --------------------------------------------------
    # Limitan el % de demanda que puede ser cubierto por residuos recuperados
    # Razones: regulatorias, técnicas, seguridad, confiabilidad
    
    for j in range(n):
        if heat_to_elec_enabled:
            # r11 × Σ_i q11[i,j] ≤ delta_heat_elec × D_j[Electricity]
            model += (
                r11 * pl.lpSum(q11[i, j] for i in range(n) if i != j) 
                <= delta_heat_elec * D_jk.iloc[j, 0]
            )
        
        if scrap_to_poly_enabled:
            # r23 × Σ_i q23[i,j] ≤ delta_scrap_poly × D_j[Polymer]
            model += (
                r23 * pl.lpSum(q23[i, j] for i in range(n) if i != j) 
                <= delta_scrap_poly * D_jk.iloc[j, 2]
            )
        
        # Steam→Water constraints would go here when implemented
        # if steam_to_water_enabled:
        #     model += (
        #         r_steam_water * pl.lpSum(q_steam[i, j] for i in range(n) if i != j)
        #         <= delta_steam_water * D_jk.iloc[j, 1]
        #     )

    # Activación de enlaces (Big-M)
    M = 1e6
    eps = 1e-6

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            model += q11[i, j] <= M * z11[i, j]
            model += q23[i, j] <= M * z23[i, j]
            model += q11[i, j] >= eps * z11[i, j]
            model += q23[i, j] >= eps * z23[i, j]

    # --------------------------------------------------
    # Función objetivo
    # --------------------------------------------------

    # Costes de insumos vírgenes (virgin input cost) - solo para sinergias habilitadas
    virgin_cost = 0
    if heat_to_elec_enabled:
        virgin_cost += cost_params["C_vir_elec"] * (D_jk.iloc[:, 0].sum() - r11 * pl.lpSum(q11.values()))
    else:
        virgin_cost += cost_params["C_vir_elec"] * D_jk.iloc[:, 0].sum()  # Sin recuperación
    
    if scrap_to_poly_enabled:
        virgin_cost += cost_params["C_vir_poly"] * (D_jk.iloc[:, 2].sum() - r23 * pl.lpSum(q23.values()))
    else:
        virgin_cost += cost_params["C_vir_poly"] * D_jk.iloc[:, 2].sum()  # Sin recuperación

    # Costes de disposición de residuos (waste disposal cost) - solo para sinergias habilitadas
    disposal_cost = 0
    if heat_to_elec_enabled:
        disposal_cost += cost_params["C_disp_heat"] * (S_il.iloc[:, 0].sum() - pl.lpSum(q11.values()))
    else:
        disposal_cost += cost_params["C_disp_heat"] * S_il.iloc[:, 0].sum()  # Todo se dispone
    
    if scrap_to_poly_enabled:
        disposal_cost += cost_params["C_disp_scrap"] * (S_il.iloc[:, 1].sum() - pl.lpSum(q23.values()))
    else:
        disposal_cost += cost_params["C_disp_scrap"] * S_il.iloc[:, 1].sum()  # Todo se dispone

    # Costes de recuperación/uso (recovery cost) - solo si están habilitadas
    recovery_cost = 0
    if heat_to_elec_enabled:
        recovery_cost += cost_params.get("C_use_heat", 0.0) * pl.lpSum(q11.values())
    if scrap_to_poly_enabled:
        recovery_cost += cost_params.get("C_use_scrap", 0.0) * pl.lpSum(q23.values())
    
    # Costes de activación fijos (activation cost) - solo si están habilitadas
    activation_cost = 0
    if heat_to_elec_enabled:
        activation_cost += cost_params.get("F_fixed_heat", 0.0) * pl.lpSum(z11.values())
    if scrap_to_poly_enabled:
        activation_cost += cost_params.get("F_fixed_scrap", 0.0) * pl.lpSum(z23.values())
    
    # Costes de transporte (transport cost) - solo si están habilitadas
    transport_cost = 0
    if heat_to_elec_enabled:
        transport_cost += pl.lpSum(
            cost_params.get("T11", 0.0) * dist_ij[i, j] * q11[i, j]
            for i, j in q11
        )
    if scrap_to_poly_enabled:
        transport_cost += pl.lpSum(
            cost_params.get("T23", 0.0) * dist_ij[i, j] * q23[i, j]
            for i, j in q23
        )

    model += virgin_cost + disposal_cost + recovery_cost + activation_cost + transport_cost

    # --------------------------------------------------
    # Resolver
    # --------------------------------------------------
    model.solve(pl.PULP_CBC_CMD(msg=0))
    status = pl.LpStatus[model.status]

    # --------------------------------------------------
    # Resultados
    # --------------------------------------------------
    q11_sol = np.zeros((n, n))
    q23_sol = np.zeros((n, n))
    z11_sol = np.zeros((n, n))
    z23_sol = np.zeros((n, n))

    for (i, j), var in q11.items():
        q11_sol[i, j] = var.varValue or 0.0
    for (i, j), var in q23.items():
        q23_sol[i, j] = var.varValue or 0.0
    for (i, j), var in z11.items():
        z11_sol[i, j] = var.varValue or 0.0
    for (i, j), var in z23.items():
        z23_sol[i, j] = var.varValue or 0.0

    # Calculate detailed cost breakdown
    total_heat_exchanged = q11_sol.sum()
    total_scrap_exchanged = q23_sol.sum()
    
    disposal_cost_heat = cost_params["C_disp_heat"] * (S_il.iloc[:, 0].sum() - total_heat_exchanged)
    disposal_cost_scrap = cost_params["C_disp_scrap"] * (S_il.iloc[:, 1].sum() - total_scrap_exchanged)
    disposal_cost_total = disposal_cost_heat + disposal_cost_scrap
    
    virgin_cost_elec = cost_params["C_vir_elec"] * (D_jk.iloc[:, 0].sum() - r11 * total_heat_exchanged)
    virgin_cost_poly = cost_params["C_vir_poly"] * (D_jk.iloc[:, 2].sum() - r23 * total_scrap_exchanged)
    virgin_cost_total = virgin_cost_elec + virgin_cost_poly
    
    # Recovery/use costs
    recovery_cost_heat = cost_params.get("C_use_heat", 0.0) * total_heat_exchanged
    recovery_cost_scrap = cost_params.get("C_use_scrap", 0.0) * total_scrap_exchanged
    recovery_cost_total = recovery_cost_heat + recovery_cost_scrap
    
    # Fixed activation costs
    active_heat_connections = z11_sol.sum()
    active_scrap_connections = z23_sol.sum()
    activation_cost_heat = cost_params.get("F_fixed_heat", 0.0) * active_heat_connections
    activation_cost_scrap = cost_params.get("F_fixed_scrap", 0.0) * active_scrap_connections
    activation_cost_total = activation_cost_heat + activation_cost_scrap
    
    # Transport costs
    transport_cost_heat = sum(
        cost_params.get("T11", 0.0) * dist_ij[i, j] * q11_sol[i, j]
        for i in range(n) for j in range(n) if i != j
    )
    transport_cost_scrap = sum(
        cost_params.get("T23", 0.0) * dist_ij[i, j] * q23_sol[i, j]
        for i in range(n) for j in range(n) if i != j
    )
    transport_cost_total = transport_cost_heat + transport_cost_scrap

    return {
        "status": status,
        "objective": pl.value(model.objective),
        "q11": q11_sol,
        "q23": q23_sol,
        "z11": z11_sol,
        "z23": z23_sol,
        "cost_breakdown": {
            "disposal_heat": disposal_cost_heat,
            "disposal_scrap": disposal_cost_scrap,
            "disposal_total": disposal_cost_total,
            "virgin_elec": virgin_cost_elec,
            "virgin_poly": virgin_cost_poly,
            "virgin_total": virgin_cost_total,
            "recovery_heat": recovery_cost_heat,
            "recovery_scrap": recovery_cost_scrap,
            "recovery_total": recovery_cost_total,
            "activation_heat": activation_cost_heat,
            "activation_scrap": activation_cost_scrap,
            "activation_total": activation_cost_total,
            "transport_heat": transport_cost_heat,
            "transport_scrap": transport_cost_scrap,
            "transport_total": transport_cost_total,
        },
    }
