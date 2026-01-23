# map.py — Professional Geographic Visualization

import folium
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from branca.element import Template, MacroElement


def create_professional_symbiosis_map(df_arcs, coords, firm_names, robustness_threshold=0.2, active_synergies=None):
    """
    Create a professional, elegant industrial symbiosis network map with:
    - High-quality CartoDB tiles
    - Color-coded exchange types (dynamically based on active synergies)
    - Robustness-based opacity
    - Flow-based line thickness
    - Professional legend with metadata
    - Interactive popups with detailed information
    
    Parameters:
    -----------
    df_arcs : DataFrame - exchange data with columns: i, j, stream, mean_q_uncond, prob_active, dist_km
    coords : dict - firm coordinates {name: (lat, lon)}
    firm_names : list - ordered firm names
    robustness_threshold : float - minimum robustness to display (0-1)
    active_synergies : list - list of active synergy names (e.g., ['heat→elec', 'scrap→poly', 'steam→water'])
    
    Returns:
    --------
    folium.Map object
    """
    
    if df_arcs.empty:
        return None
    
    # Define professional color palette (colorblind-friendly)
    # Dynamically assign colors based on active synergies
    available_colors = ["#0077B6", "#FF6B35", "#28A745", "#FFC107", "#E74C3C"]
    
    # Get unique streams from the data (these are the actually active synergies)
    unique_streams = df_arcs["stream"].unique().tolist()
    
    # Assign colors dynamically
    stream_colors = {}
    for idx, stream in enumerate(unique_streams):
        stream_colors[stream] = available_colors[idx % len(available_colors)]
    
    # Calculate map center
    lats = [coords[name][0] for name in firm_names]
    lons = [coords[name][1] for name in firm_names]
    
    m = folium.Map(
        location=[np.mean(lats), np.mean(lons)],
        zoom_start=12,
        tiles="CartoDB positron",
        prefer_canvas=True
    )
    
    # Add basemap control
    folium.TileLayer("CartoDB voyager", name="Voyager").add_to(m)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    
    # =============================================
    # FIRM MARKERS (Professional styling)
    # =============================================
    fg_firms = folium.FeatureGroup(name="🏭 Industrial Facilities", show=True)
    
    for idx, name in enumerate(firm_names):
        lat, lon = coords[name]
        
        # Create professional popup
        popup_html = f"""
        <div style="font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif; width:220px;">
            <h4 style="color:#0077B6; margin:0 0 8px 0; border-bottom:2px solid #0077B6; padding-bottom:5px;">
                {name}
            </h4>
            <div style="font-size:11px; color:#333;">
                <b>Location:</b><br>
                Lat: {lat:.4f}, Lon: {lon:.4f}<br><br>
                <b>Data Source:</b> Real Data ✓
            </div>
        </div>
        """
        
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=name,
            icon=folium.Icon(
                icon="industry",
                prefix="fa",
                color="darkblue",
                icon_color="white"
            )
        ).add_to(fg_firms)
    
    fg_firms.add_to(m)
    
    # =============================================
    # EXCHANGE CONNECTIONS (Professional styling)
    # =============================================
    
    # Create feature groups per stream
    stream_groups = {}
    for stream in df_arcs["stream"].unique():
        stream_groups[stream] = folium.FeatureGroup(
            name=f"💱 {stream}",
            show=True
        )
        stream_groups[stream].add_to(m)
    
    # Calculate scaling factors
    max_flow = df_arcs["mean_q_uncond"].max() if len(df_arcs) > 0 else 1.0
    
    # Process connections
    for _, row in df_arcs.iterrows():
        # Skip low-robustness exchanges
        if row["prob_active"] < robustness_threshold:
            continue
        
        i, j = int(row["i"]), int(row["j"])
        stream = row["stream"]
        origin = firm_names[i]
        dest = firm_names[j]
        flow = float(row["mean_q_uncond"])
        prob = float(row["prob_active"])
        distance = float(row["dist_km"])
        
        # Get optional quantile data
        p10 = row.get("p10_cond", np.nan)
        p50 = row.get("p50_cond", np.nan)
        p90 = row.get("p90_cond", np.nan)
        
        # Professional popup with rich formatting
        popup_html = f"""
        <div style="font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif; width:280px;">
            <h5 style="color:{stream_colors.get(stream, '#333')}; margin:0 0 10px 0; 
                       border-bottom:2px solid {stream_colors.get(stream, '#ddd')}; padding-bottom:5px;">
                {stream}
            </h5>
            
            <div style="font-size:12px; color:#333; line-height:1.6;">
                <b>Connection:</b><br>
                <span style="color:#0077B6; font-weight:bold;">{origin}</span> 
                <span style="color:#666;">→</span> 
                <span style="color:#0077B6; font-weight:bold;">{dest}</span><br><br>
                
                <b>Flow Characteristics:</b><br>
                • Expected: <span style="color:#FF6B35; font-weight:bold;">{flow:.3f}</span><br>
                • Distance: <span style="font-weight:bold;">{distance:.2f} km</span><br><br>
                
                <b>Robustness Analysis:</b><br>
                • Probability: <span style="color:{'#2ecc71' if prob > 0.7 else '#f39c12' if prob > 0.4 else '#e74c3c'}; 
                                            font-weight:bold;">{prob*100:.1f}%</span><br>
        """
        
        if not np.isnan(p10) and not np.isnan(p50) and not np.isnan(p90):
            popup_html += f"""
                • P10 (cond): {p10:.3f}<br>
                • P50 (cond): {p50:.3f}<br>
                • P90 (cond): {p90:.3f}<br>
            """
        
        popup_html += """
            </div>
        </div>
        """
        
        # Line styling based on flow and robustness
        line_width = 2 + (6 * flow / max_flow) if max_flow > 0 else 2
        line_opacity = 0.4 + (0.6 * prob)  # 0.4 to 1.0 based on probability
        
        # Dashed line if low robustness
        dash_array = "8, 4" if prob < 0.5 else None
        
        folium.PolyLine(
            locations=[coords[origin], coords[dest]],
            color=stream_colors.get(stream, "#333"),
            weight=line_width,
            opacity=line_opacity,
            dash_array=dash_array,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{origin} → {dest}: {stream}"
        ).add_to(stream_groups[stream])
    
    # =============================================
    # PROFESSIONAL LEGEND (DYNAMIC)
    # =============================================
    
    # Build legend items dynamically based on active streams
    stream_legend_items = ""
    stream_labels = {
        "heat→elec": "Heat → Electricity",
        "scrap→poly": "Scrap → Polymer",
        "steam→water": "Steam → Water"
    }
    
    for stream, color in stream_colors.items():
        label = stream_labels.get(stream, stream)
        stream_legend_items += f"""
            <div style="display: flex; align-items: center; margin: 4px 0;">
                <span style="width: 20px; height: 3px; background: {color}; display: inline-block; margin-right: 10px;"></span>
                <span>{label}</span>
            </div>
        """
    
    legend_html = f"""
    {{% macro html(this, kwargs) %}}
    <div id="maplegend"
         style="
         position: fixed;
         z-index: 9999;
         bottom: 20px;
         left: 20px;
         width: 320px;
         background: rgba(255, 255, 255, 0.95);
         border: 1px solid #ddd;
         border-radius: 6px;
         padding: 16px;
         font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
         font-size: 12px;
         color: #333;
         box-shadow: 0 4px 20px rgba(0,0,0,0.12);
         ">
        
        <div style="font-size: 16px; font-weight: bold; margin-bottom: 12px; color: #0077B6;">
            📊 INDUSTRIAL SYMBIOSIS NETWORK
        </div>
        
        <div style="margin-bottom: 14px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
            <div style="font-weight: bold; margin-bottom: 6px; color: #0077B6;">Exchange Types (Color):</div>
            {stream_legend_items}
        </div>
        
        <div style="margin-bottom: 14px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
            <div style="font-weight: bold; margin-bottom: 6px; color: #0077B6;">Line Characteristics:</div>
            <div style="font-size: 11px; color: #666; line-height: 1.5;">
                <b>Thickness</b> = Average flow quantity<br>
                <b>Opacity</b> = Robustness (probability)<br>
                <b>Dashed</b> = Low robustness (&lt;50%)
            </div>
        </div>
        
        <div style="margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
            <div style="font-weight: bold; margin-bottom: 6px; color: #0077B6;">Robustness Scale:</div>
            <div style="display: flex; align-items: center; margin: 3px 0; font-size: 11px;">
                <span style="width: 16px; height: 16px; background: #2ecc71; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
                <span>Strong (≥70%)</span>
            </div>
            <div style="display: flex; align-items: center; margin: 3px 0; font-size: 11px;">
                <span style="width: 16px; height: 16px; background: #f39c12; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
                <span>Moderate (40-70%)</span>
            </div>
            <div style="display: flex; align-items: center; margin: 3px 0; font-size: 11px;">
                <span style="width: 16px; height: 16px; background: #e74c3c; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
                <span>Weak (&lt;40%)</span>
            </div>
        </div>
        
        <div style="font-size: 10px; color: #999; text-align: center;">
            Click connections for details
        </div>
    </div>
    {{% endmacro %}}
    """
    
    macro = MacroElement()
    macro._template = Template(legend_html)
    m.get_root().add_child(macro)
    
    # Add layer control
    folium.LayerControl(collapsed=False, position="topright").add_to(m)
    
    return m


def create_connections_table(df_arcs, firm_names, robustness_threshold=0.2):
    """
    Create a professional connections table with sorting and filtering.
    """
    
    if df_arcs.empty:
        return pd.DataFrame()
    
    # Filter by robustness
    df_filtered = df_arcs[df_arcs["prob_active"] >= robustness_threshold].copy()
    
    # Map indices to firm names
    df_filtered["From"] = df_filtered["i"].astype(int).map(lambda x: firm_names[x])
    df_filtered["To"] = df_filtered["j"].astype(int).map(lambda x: firm_names[x])
    
    # Format for display
    df_display = df_filtered[[
        "From", "To", "stream",
        "mean_q_uncond", "prob_active", "dist_km",
        "p10_cond", "p50_cond", "p90_cond"
    ]].copy()
    
    df_display.columns = [
        "From Firm", "To Firm", "Exchange Type",
        "Avg Flow", "Robustness %", "Distance (km)",
        "P10", "P50", "P90"
    ]
    
    # Format numeric columns
    df_display["Robustness %"] = (df_display["Robustness %"] * 100).round(1).astype(str) + "%"
    df_display["Avg Flow"] = df_display["Avg Flow"].round(3)
    df_display["Distance (km)"] = df_display["Distance (km)"].round(2)
    df_display["P10"] = df_display["P10"].round(3)
    df_display["P50"] = df_display["P50"].round(3)
    df_display["P90"] = df_display["P90"].round(3)
    
    return df_display.sort_values("Avg Flow", ascending=False)


