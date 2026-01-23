import numpy as np
import pandas as pd
from optimizer import solve_milp

def run_montecarlo(
    S_il_base,
    D_jk_base,
    dist_ij,
    firm_names,
    cost_params=None,
    r11=0.9,
    r23=0.8,
    synergy_matrix=None,
    delta_heat_elec=1.0,
    delta_scrap_poly=1.0,
    delta_steam_water=1.0,
    n_sim=100,
    variation_pct=10,
    distribution_type="uniform"
):
    """
    Run Monte Carlo simulation for industrial symbiosis.
    
    Parameters:
    -----------
    S_il_base : array - baseline supply matrix
    D_jk_base : array - baseline demand matrix
    dist_ij : array - distance matrix
    firm_names : list - firm names
    cost_params : dict - cost parameters
    r11 : float - recovery rate for heat->electricity (0-1)
    r23 : float - recovery rate for scrap->polymer (0-1)
    synergy_matrix : DataFrame - enabled synergies
    delta_heat_elec : float - max substitution share for electricity from heat (0-1)
    delta_scrap_poly : float - max substitution share for polymer from scrap (0-1)
    delta_steam_water : float - max substitution share for water from steam (0-1)
    n_sim : int - number of simulations
    variation_pct : float - variation percentage (e.g., 10 for ±10%)
    distribution_type : str - "uniform" or "normal"
    
    Returns:
    --------
    df_runs : DataFrame - results per scenario
    df_qz : DataFrame - aggregate statistics
    sols : list - solver results
    df_arcs : DataFrame - all arc details
    """
    from cost_params import DEFAULT_COST_PARAMS
    
    if cost_params is None:
        cost_params = DEFAULT_COST_PARAMS
    
    n = S_il_base.shape[0]
    results = []
    arcs = []
    sols = []
    scenarios_sd = []  # Store S and D pairs for each scenario

    for sid in range(n_sim):
        np.random.seed(sid)
        
        # Generate variation factors based on distribution type
        if distribution_type == "uniform":
            # Uniform: ±variation_pct
            factor_low = 1 - (variation_pct / 100)
            factor_high = 1 + (variation_pct / 100)
            s_factor = np.random.uniform(factor_low, factor_high, S_il_base.shape)
            d_factor = np.random.uniform(factor_low, factor_high, D_jk_base.shape)
        else:  # normal
            # Normal: mean=1, std=variation_pct/100 (so ±1 std ≈ ±variation_pct)
            s_factor = np.random.normal(1.0, variation_pct / 100, S_il_base.shape)
            d_factor = np.random.normal(1.0, variation_pct / 100, D_jk_base.shape)
            # Clip to avoid negative values
            s_factor = np.maximum(s_factor, 0.1)
            d_factor = np.maximum(d_factor, 0.1)
        
        # Apply variation
        S_il_varied = S_il_base * s_factor
        D_jk_varied = D_jk_base * d_factor
        
        # Store S and D for this scenario
        scenarios_sd.append({
            "scenario_id": sid,
            "S_il": S_il_varied.copy(),
            "D_jk": D_jk_varied.copy()
        })
        
        # Convert to DataFrame format for solver
        # Now S_il has 3 columns: Heat, Scrap, Steam
        S_il_df = pd.DataFrame(S_il_varied, index=[f"F{i+1}" for i in range(n)], columns=["Heat", "Scrap", "Steam"])
        # D_jk has 3 columns: Electricity, Water, Polymer
        D_jk_df = pd.DataFrame(D_jk_varied, index=[f"F{i+1}" for i in range(n)], columns=["Electricity", "Water", "Polymer"])

        try:
            # Call real MILP solver with synergy configuration and delta constraints
            res = solve_milp(
                S_il=S_il_df,
                D_jk=D_jk_df,
                dist_ij=dist_ij,
                cost_params=cost_params,
                r11=r11,
                r23=r23,
                synergy_matrix=synergy_matrix,
                delta_heat_elec=delta_heat_elec,
                delta_scrap_poly=delta_scrap_poly,
                delta_steam_water=delta_steam_water
            )
        except Exception as e:
            print(f"Warning: Solver failed for scenario {sid}: {str(e)}")
            res = {
                "status": "failed",
                "objective": 0.0,
                "q11": np.zeros((n, n)),
                "q23": np.zeros((n, n)),
                "z11": np.zeros((n, n)),
                "z23": np.zeros((n, n)),
            }

        sols.append(res)
        q11 = res["q11"]
        q23 = res["q23"]
        z11 = res["z11"]
        z23 = res["z23"]
        
        # Count active arcs
        active_arcs_count = 0
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                if z11[i, j] > 0.5:
                    active_arcs_count += 1
                if z23[i, j] > 0.5:
                    active_arcs_count += 1

        results.append({
            "scenario_id": sid,
            "status": res["status"],
            "objective_total": res["objective"],
            "total_heat_used": q11.sum(),
            "total_scrap_used": q23.sum(),
            "active_arcs": active_arcs_count,
        })

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                if z11[i, j] > 0.5:
                    arcs.append({
                        "scenario_id": sid,
                        "i": i,
                        "j": j,
                        "stream": "heat→elec",
                        "q": q11[i, j],
                        "active": 1,
                        "dist_km": dist_ij[i, j]
                    })
                if z23[i, j] > 0.5:
                    arcs.append({
                        "scenario_id": sid,
                        "i": i,
                        "j": j,
                        "stream": "scrap→poly",
                        "q": q23[i, j],
                        "active": 1,
                        "dist_km": dist_ij[i, j]
                    })

    df_runs = pd.DataFrame(results)
    df_arcs = pd.DataFrame(arcs)

    if not df_arcs.empty:
        grouped = df_arcs.groupby(["i", "j", "stream"])
        df_qz = grouped.agg(
            mean_q_uncond=("q", "mean"),
            prob_active=("active", "mean"),
            dist_km=("dist_km", "mean")
        ).reset_index()

        # Conditional quantiles for q|active
        quantiles = grouped["q"].quantile([0.1, 0.5, 0.9]).unstack()
        quantiles.columns = ["p10_cond", "p50_cond", "p90_cond"]
        df_qz = df_qz.merge(quantiles, on=["i", "j", "stream"])
    else:
        df_qz = pd.DataFrame(columns=["i", "j", "stream", "mean_q_uncond", "prob_active", "dist_km", "p10_cond", "p50_cond", "p90_cond"])

    return df_runs, df_qz, sols, df_arcs, scenarios_sd



