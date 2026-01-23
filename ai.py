# ai.py — recomendaciones y advertencias inteligentes
import pandas as pd
import numpy as np

def add_data_quality_flags(df_flags):
    """Add quality indicators to data source flags"""
    df_flags = df_flags.copy()
    df_flags["Quality"] = df_flags["DataSource"].apply(lambda x: "✅ Real" if x == "REAL" else "⚠️ Estimated")
    return df_flags

def compute_robustness_scores(df_qz):
    """
    Compute robustness scores for each exchange (0-1).
    Higher prob_active = more robust
    """
    if df_qz.empty:
        return pd.DataFrame()
    
    df_rob = df_qz[["i", "j", "stream", "prob_active"]].copy()
    df_rob["robustness"] = df_rob["prob_active"]
    df_rob["robustness_label"] = df_rob["robustness"].apply(lambda x: 
        "🟢 Highly Robust (>90%)" if x > 0.9 else
        "🟡 Moderate (50-90%)" if x > 0.5 else
        "🔴 Risky (<50%)"
    )
    return df_rob

def generate_partnership_recommendations(df_qz, firm_names=None):
    """
    Generate smart partnership recommendations based on robustness.
    """
    if df_qz.empty:
        return []
    
    recommendations = []
    
    # Sort by robustness
    df_sorted = df_qz.sort_values("prob_active", ascending=False)
    
    for _, row in df_sorted.iterrows():
        i, j = int(row["i"]), int(row["j"])
        prob = row["prob_active"]
        stream = row["stream"]
        
        # Skip very weak exchanges
        if prob < 0.2:
            continue
        
        firm_i = firm_names[i] if firm_names else f"F{i+1}"
        firm_j = firm_names[j] if firm_names else f"F{j+1}"
        
        # Create recommendation
        if prob > 0.8:
            confidence = "STRONG ✅"
            action = "Implement immediately"
        elif prob > 0.5:
            confidence = "MODERATE 🟡"
            action = "Further develop"
        else:
            confidence = "WEAK 🔴"
            action = "Monitor potential"
        
        quantity = row.get("mean_q_uncond", 0)
        distance = row.get("dist_km", 0)
        
        rec = {
            "From": firm_i,
            "To": firm_j,
            "Stream": stream,
            "Probability": f"{prob*100:.1f}%",
            "Confidence": confidence,
            "Action": action,
            "Avg Quantity": f"{quantity:.2f}",
            "Distance (km)": f"{distance:.2f}"
        }
        recommendations.append(rec)
    
    return recommendations

def generate_data_quality_report(df_flags):
    """
    Generate report on data quality across firms.
    Recommend which firms need real data collection.
    """
    report = []
    
    for _, row in df_flags.iterrows():
        firm = row["Firm"]
        source = row["DataSource"]
        quality = "✅ Real data" if source == "REAL" else "⚠️ EIO estimated"
        
        priority = "LOW" if source == "REAL" else "HIGH"
        action = "Continue monitoring" if source == "REAL" else "Collect real data"
        
        report.append({
            "Firm": firm,
            "Data Source": quality,
            "Priority for Data Collection": priority,
            "Recommended Action": action
        })
    
    return pd.DataFrame(report)

def global_warnings_and_insights(df_runs, df_flags, df_qz=None):
    """
    Generate global warnings and insights from simulation results.
    """
    warnings = []
    insights = []
    
    # Check solver status (case-insensitive)
    n_failed = sum(df_runs["status"].str.lower() != "optimal")
    if n_failed > 0:
        warnings.append(f"⚠️ {n_failed}/{len(df_runs)} simulations failed to converge")
    else:
        insights.append("✅ All simulations converged successfully")
    
    # Check data quality
    if "DataSource" in df_flags.columns:
        n_eio = sum(df_flags["DataSource"] == "EIO")
        n_total = len(df_flags)
        if n_eio > 0:
            pct = (n_eio / n_total * 100)
            warnings.append(f"⚠️ {n_eio}/{n_total} firms ({pct:.0f}%) use estimated EIO data")
        else:
            insights.append("✅ All firms have real data")
    
    # Check exchange robustness
    if df_qz is not None and not df_qz.empty:
        n_robust = sum(df_qz["prob_active"] > 0.8)
        n_risky = sum(df_qz["prob_active"] < 0.5)
        n_total_exchanges = len(df_qz)
        
        if n_robust > 0:
            insights.append(f"✅ {n_robust} highly robust exchanges identified")
        if n_risky > 0:
            warnings.append(f"⚠️ {n_risky} risky exchanges (low robustness)")
    
    # Check variability
    if "objective_total" in df_runs.columns:
        std_obj = df_runs["objective_total"].std()
        mean_obj = df_runs["objective_total"].mean()
        cv = (std_obj / mean_obj * 100) if mean_obj > 0 else 0
        
        if cv < 10:
            insights.append(f"✅ Low cost variability ({cv:.1f}%) - stable network")
        elif cv > 30:
            warnings.append(f"⚠️ High cost variability ({cv:.1f}%) - unstable to demand changes")
    
    return {
        "warnings": warnings,
        "insights": insights
    }


