# firms.py — inserta datos reales y construye S_il y D_jk

import numpy as np
import pandas as pd

from model import R0, W0, Y, sectors_short

def build_firm_matrices(x, real_firms={}):
    # Baseline estimado (EIO)
    S_il_eio = (W0.T * x[:, None])
    D_jk_eio = (R0.T * x[:, None])

    df_S_il = pd.DataFrame(S_il_eio, index=sectors_short, columns=["Waste heat", "Plastic scrap"])
    df_D_jk = pd.DataFrame(D_jk_eio, index=sectors_short, columns=["Electricity", "Water", "Virgin polymer"])

    # Insertar datos reales si se dan
    for firm, data in real_firms.items():
        if "S" in data:
            df_S_il.loc[firm] = data["S"]
        if "D" in data:
            df_D_jk.loc[firm] = data["D"]

    # Etiquetas EIO / REAL
    flags = []
    for f in sectors_short:
        if f in real_firms:
            flags.append("REAL")
        else:
            flags.append("EIO")

    df_flags = pd.DataFrame({
        "Firm": sectors_short,
        "DataSource": flags
    })

    return df_S_il, df_D_jk, df_flags


# Cargar por defecto para app
df_S_il, df_D_jk, df_flags = build_firm_matrices(
    x=Y,
    real_firms={
        "F1": {
            "S": [0.2, 0.1],
            "D": [1.0, 2.0, 0.3]
        },
        "F3": {
            "D": [1.5, 1.0, 1.0]
        }
    }
)

