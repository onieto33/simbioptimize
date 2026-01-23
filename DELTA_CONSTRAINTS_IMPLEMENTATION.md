# δ (Delta) Substitution Share Constraints - Implementation

## 📋 Overview

This document explains the implementation of **Maximum Substitution Rate (δ)** constraints in the industrial symbiosis optimization model.

## 🎯 Purpose

The δ constraints ensure that waste-derived inputs don't exceed realistic technical, regulatory, or safety limits. Without these constraints, the optimizer might propose **100% substitution** when only **30-80% is practically feasible**.

## 📐 Mathematical Formulation

For each receiving firm $j$ and each enabled synergy $(l \rightarrow k)$:

$$r_{lk} \times \sum_{i \neq j} q_{ij}^{lk} \leq \delta_{lk} \times D_j^k$$

Where:
- $r_{lk}$: Recovery/conversion efficiency (e.g., 0.9 = 90% efficient)
- $q_{ij}^{lk}$: Flow of waste $l$ from firm $i$ to firm $j$ for conversion to input $k$
- $\delta_{lk}$: Maximum substitution share (0-1, e.g., 0.8 = max 80% from waste)
- $D_j^k$: Total demand of input $k$ at firm $j$

**Interpretation:**
- Left side: Amount of input $k$ recovered from waste flows
- Right side: Maximum allowed from waste (δ × total demand)

## 🏭 Application in the Model

### Heat → Electricity
```python
# For each firm j receiving electricity:
r11 × Σ(q11[i,j] for i≠j) ≤ delta_heat_elec × D_jk[j, "Electricity"]
```

**Example:**
- Firm has demand: 100 MWh electricity
- δ = 0.8 (80% max from waste)
- γ (r11) = 0.9 (90% conversion efficiency)
- **Max recovered**: 80 MWh electricity
- **Max heat flow needed**: 80 / 0.9 = 88.9 MWh heat
- **Min virgin electricity**: 20 MWh (from grid)

### Scrap → Polymer
```python
# For each firm j receiving polymer:
r23 × Σ(q23[i,j] for i≠j) ≤ delta_scrap_poly × D_jk[j, "Polymer"]
```

**Example:**
- Firm has demand: 50 tons polymer
- δ = 0.7 (70% max recycled due to quality specs)
- γ (r23) = 0.8 (80% conversion efficiency)
- **Max recovered**: 35 tons polymer
- **Max scrap needed**: 35 / 0.8 = 43.75 tons scrap
- **Min virgin polymer**: 15 tons

### Steam → Water (when implemented)
```python
# For each firm j receiving water:
r_steam × Σ(q_steam[i,j] for i≠j) ≤ delta_steam_water × D_jk[j, "Water"]
```

## 🔧 Implementation Details

### 1. Function Signature (optimizer.py)
```python
def solve_milp(
    S_il, D_jk, dist_ij, cost_params,
    r11=0.9, r23=0.8,
    synergy_matrix=None,
    delta_heat_elec=1.0,    # NEW
    delta_scrap_poly=1.0,   # NEW
    delta_steam_water=1.0,  # NEW
):
```

### 2. Constraint Generation (optimizer.py)
```python
# Substitution Share Constraints
for j in range(n):
    if heat_to_elec_enabled:
        model += (
            r11 * pl.lpSum(q11[i, j] for i in range(n) if i != j) 
            <= delta_heat_elec * D_jk.iloc[j, 0]
        )
    
    if scrap_to_poly_enabled:
        model += (
            r23 * pl.lpSum(q23[i, j] for i in range(n) if i != j) 
            <= delta_scrap_poly * D_jk.iloc[j, 2]
        )
```

### 3. UI Integration (streamlit_app.py)
- **Input**: Sliders in Tab 2 "Data Matrices" (key: `delta_heat_elec_matrix`, etc.)
- **Storage**: `st.session_state.get("delta_heat_elec_matrix", 1.0)`
- **Passing**: Through `run_montecarlo()` → `solve_milp()`

### 4. Parameter Flow
```
User adjusts slider → Session state → run_montecarlo() → solve_milp() → MILP constraint
```

## 📊 Impact Analysis

### Without δ Constraints
```
Solution: 100% electricity from waste heat
Problem: May violate grid stability requirements
```

### With δ = 0.8 Constraints
```
Solution: Max 80% electricity from waste heat
Result: More realistic, compliant with regulations
Cost: Slightly higher (more virgin inputs needed)
```

## 🎛️ Default Values

| Parameter | Default | Range | Typical Industrial Values |
|-----------|---------|-------|--------------------------|
| `delta_heat_elec` | 0.8 | 0.0-1.0 | 0.6-0.9 (grid stability) |
| `delta_scrap_poly` | 0.8 | 0.0-1.0 | 0.5-0.8 (quality specs) |
| `delta_steam_water` | 0.8 | 0.0-1.0 | 0.7-0.95 (health regs) |

**Note:** δ = 1.0 means no limit (100% substitution allowed, backward compatible)

## 🔍 Testing & Validation

### Test Case 1: Full Substitution Blocked
```python
# Setup
D_elec = 100 MWh
delta = 0.7
r11 = 0.9

# Expected
Max recovered electricity = 70 MWh
Max heat flow = 70 / 0.9 = 77.78 MWh
Min virgin electricity = 30 MWh
```

### Test Case 2: Supply-Limited (δ not binding)
```python
# Setup
Available heat = 50 MWh
D_elec = 100 MWh
delta = 0.8
r11 = 0.9

# Expected
Max recovered = 50 × 0.9 = 45 MWh (supply limit binds)
Virgin electricity = 55 MWh
Delta constraint: 45 ≤ 0.8 × 100 = 80 ✓ (not binding)
```

## 🚀 Benefits

1. **Realism**: Solutions respect actual industrial constraints
2. **Compliance**: Ensures regulatory compliance (e.g., max recycled content)
3. **Reliability**: Maintains supply diversity (avoid single-source dependency)
4. **Flexibility**: Users can adjust δ based on specific context

## 📚 Literature Support

This implementation aligns with:
- **Boix et al. (2015)**: Quality constraints in resource exchange networks
- **Yazan et al. (2020)**: Technical feasibility limits in industrial symbiosis
- **EU Circular Economy Directive**: Maximum recycled content in certain products

## ⚠️ Known Limitations

1. **Steam→Water not yet implemented**: Variables don't exist yet (q_steam)
2. **Firm-specific δ**: Currently global per synergy, could be firm-specific
3. **Time-varying δ**: Static in current model, could evolve over time

## 🔄 Future Enhancements

1. **Firm-specific limits**: `delta_heat_elec[j]` instead of global `delta_heat_elec`
2. **Product-specific limits**: Different δ for different polymer grades
3. **Temporal dynamics**: δ increases as technology matures
4. **Certification tracking**: Binary variable for "certified recycled" vs "standard"

---

**Implementation Date:** January 22, 2026  
**Status:** ✅ Fully Implemented for Heat→Electricity and Scrap→Polymer  
**Next Steps:** Implement Steam→Water synergy variables
