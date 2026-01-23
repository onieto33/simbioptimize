# geo.py — contiene coordenadas y matriz de distancias
import numpy as np
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

# Asignación de nombres y códigos
sectors_short = ["F1", "F2", "F3", "F4", "F5"]
firm_map = {
    "F1": "Dikar",
    "F2": "Onnera",
    "F3": "Ecenarro",
    "F4": "FagorArrasate",
    "F5": "Ausolan"
}
firm_names = [firm_map[f] for f in sectors_short]

# Coordenadas (puedes editarlas según necesidad)
coords = {
    "Dikar": (43.064, -2.487),
    "Onnera": (43.066, -2.491),
    "Ecenarro": (43.061, -2.485),
    "FagorArrasate": (43.050, -2.520),
    "Ausolan": (43.045, -2.530)
}

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def build_distance_matrix(coords_dict):
    names = list(coords_dict.keys())
    n = len(names)
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            lat1, lon1 = coords_dict[names[i]]
            lat2, lon2 = coords_dict[names[j]]
            dist[i, j] = haversine_km(lat1, lon1, lat2, lon2)
    return dist, names

# Matriz de distancias
dist_ij, firm_order = build_distance_matrix(coords)

# DataFrame para facilitar uso
df_distances = pd.DataFrame(dist_ij, index=firm_order, columns=firm_order)
