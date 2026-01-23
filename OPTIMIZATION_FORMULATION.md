# 📐 Problema de Optimización: Simbiosis Industrial

## Formulación Matemática Completa

### Función Objetivo

$$
\min_{q_{lk}, z_{lk}} \Bigg\{
\underbrace{
\sum_{k \in \mathcal{K}} C_k^{\mathrm{vir}}
\left(
D_k - \sum_{l:\, k \in \mathcal{F}_l} \gamma_{lk} q_{lk}
\right)
}_{\text{virgin input cost}}
+
\underbrace{
\sum_{l \in \mathcal{L}} C_l^{\mathrm{disp}}
\left(
S_l - \sum_{k \in \mathcal{F}_l} q_{lk}
\right)
}_{\text{waste disposal cost}}
+
\underbrace{
\sum_{l \in \mathcal{L}} \sum_{k \in \mathcal{F}_l}
C_{lk}^{\mathrm{use}} q_{lk}
}_{\text{recovery cost}}
+
\underbrace{
\sum_{l \in \mathcal{L}} \sum_{k \in \mathcal{F}_l}
F_{lk} z_{lk}
}_{\text{activation cost}}
+
\underbrace{
\sum_{l \in \mathcal{L}} \sum_{k \in \mathcal{F}_l}
T_{lk} \cdot d_{ij} \cdot q_{lk}
}_{\text{transport cost}}
\Bigg\}
$$

---

## Implementación en el Código

### Índices y Conjuntos

- **Firmas**: i, j ∈ {1, 2, 3, 4, 5}
- **Recursos (l)**: 
  - l=1: Calor residual (Heat)
  - l=2: Scrap plástico (Scrap)
- **Insumos (k)**:
  - k=1: Electricidad (Electricity)
  - k=2: Polímero virgen (Polymer)

### Variables de Decisión

**Continuas:**
- `q11[i,j]` ≥ 0: Cantidad de calor de i a j (MWh)
- `q23[i,j]` ≥ 0: Cantidad de scrap de i a j (tons)

**Binarias:**
- `z11[i,j]` ∈ {0,1}: Conexión de calor activa
- `z23[i,j]` ∈ {0,1}: Conexión de scrap activa

### Parámetros

**Datos de Entrada:**
- `S_il[i,l]`: Suministro de recurso l en firma i
  - `S_il[i,0]`: Calor disponible (MWh)
  - `S_il[i,1]`: Scrap disponible (tons)
- `D_jk[j,k]`: Demanda de insumo k en firma j
  - `D_jk[j,0]`: Electricidad necesaria (MWh)
  - `D_jk[j,2]`: Polímero necesario (tons)

**Eficiencias de Conversión (γ):**
- `r11` = 0.9: Calor → Electricidad (90%)
- `r23` = 0.8: Scrap → Polímero (80%)

**Distancias:**
- `dist_ij[i,j]`: Distancia entre firmas i y j (km)

---

## Componentes de Costo (TODOS Incluidos)

### 1. Virgin Input Cost (Costos de Insumos Vírgenes)
```
C_vir_elec × (Total_Elec_Demand - r11 × Total_Heat_Exchanged)
+ C_vir_poly × (Total_Poly_Demand - r23 × Total_Scrap_Exchanged)
```

### 2. Waste Disposal Cost (Costos de Disposición)
```
C_disp_heat × (Total_Heat_Available - Total_Heat_Exchanged)
+ C_disp_scrap × (Total_Scrap_Available - Total_Scrap_Exchanged)
```

### 3. Recovery Cost (Costos de Recuperación)
```
C_use_heat × Total_Heat_Exchanged
+ C_use_scrap × Total_Scrap_Exchanged
```

### 4. Activation Cost (Costos de Activación Fijos)
```
F_fixed_heat × Number_of_Heat_Connections
+ F_fixed_scrap × Number_of_Scrap_Connections
```

### 5. Transport Cost (Costos de Transporte)
```
∑(i,j) T11 × dist_ij × q11[i,j]
+ ∑(i,j) T23 × dist_ij × q23[i,j]
```

---

## Parámetros de Costo

Todos los parámetros se usan simultáneamente:

- **Virgin Inputs:**
  - `C_vir_elec` = 80 €/MWh
  - `C_vir_poly` = 1200 €/ton

- **Disposal:**
  - `C_disp_heat` = 5 €/MWh
  - `C_disp_scrap` = 50 €/ton

- **Recovery/Use:**
  - `C_use_heat` = 2 €/MWh
  - `C_use_scrap` = 20 €/ton

- **Fixed Activation:**
  - `F_fixed_heat` = 500 €
  - `F_fixed_scrap` = 800 €

- **Transport:**
  - `T11` = 0.5 €/(MWh·km)
  - `T23` = 10 €/(ton·km)

---

## Restricciones

### 1. Capacidad de Suministro
```
∑j q11[i,j] ≤ S_il[i,0]    ∀i  (calor)
∑j q23[i,j] ≤ S_il[i,1]    ∀i  (scrap)
```

### 2. Límites de Demanda
```
r11 × ∑i q11[i,j] ≤ D_jk[j,0]    ∀j  (electricidad)
r23 × ∑i q23[i,j] ≤ D_jk[j,2]    ∀j  (polímero)
```

### 3. Activación de Enlaces (Big-M)
```
q11[i,j] ≤ M × z11[i,j]
q11[i,j] ≥ ε × z11[i,j]
q23[i,j] ≤ M × z23[i,j]
q23[i,j] ≥ ε × z23[i,j]
```
Donde: M = 10⁶, ε = 10⁻⁶

---

## Solver

- **Tipo**: MILP (Mixed Integer Linear Programming)
- **Solver**: CBC (COIN-OR Branch and Cut)
- **Librería**: PuLP (Python)

---

## Configuración en la Interfaz

En la pestaña **"⚙️ Optimization"**, el usuario puede:

1. **Configurar simulación Monte Carlo**:
   - Número de escenarios (10-500)
   - Variación de incertidumbre (±%)
   - Tipo de distribución (uniforme/normal)

2. **Ajustar parámetros de costo** en la pestaña **"⚙️ Cost Parameters"**:
   - Todos los 10 parámetros de costo se aplican simultáneamente
   - Cada parámetro puede ajustarse individualmente

3. **Ver desglose completo** de los 5 componentes de costo:
   - Virgin Input Costs
   - Disposal Costs
   - Recovery Costs
   - Activation Costs
   - Transport Costs

---

## Salidas del Modelo

Para cada escenario optimizado:
- Matrices `q11`, `q23`: Flujos óptimos
- Matrices `z11`, `z23`: Conexiones activas
- Costo total y desglose por componente
- Métricas de red (arcos activos, utilización de recursos)
