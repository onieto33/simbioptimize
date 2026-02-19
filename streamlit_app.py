import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
from math import radians, sin, cos, sqrt, atan2
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from firms import build_firm_matrices
from model import baseline, df_S_il_eoi, df_D_jk_eoi
from geo import firm_map, coords, haversine_km
from montecarlo import run_montecarlo
from optimizer import solve_milp
from cost_params import DEFAULT_COST_PARAMS, COST_RANGES, COST_DESCRIPTIONS
from ai import (
    add_data_quality_flags,
    compute_robustness_scores,
    generate_partnership_recommendations,
    generate_data_quality_report,
    global_warnings_and_insights
)
from map import create_professional_symbiosis_map, create_connections_table

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="SIMBIOPTIMIZE",
    page_icon="LogoSymbiosis.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS FOR PROFESSIONAL LOOK
# ============================================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .main-subtitle {
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.95;
    }
    .firm-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# INITIALIZE SESSION STATE
# ============================================
# Initialize show_landing flag (default: show landing page)
if "show_landing" not in st.session_state:
    st.session_state.show_landing = True

# ============================================
# LANDING PAGE / PORTADA
# ============================================
if st.session_state.show_landing:
    # Convert logos to base64 for HTML embedding
    import os
    import base64
    
    # Try to load and encode the platform logo
    logo_html = ""
    try:
        platform_logo = "LogoSymbiosis.jpg"
        if os.path.exists(platform_logo):
            with open(platform_logo, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode()
                logo_html = f'<img src="data:image/jpeg;base64,{encoded}" style="width: 450px; max-width: 90%; margin: 2rem auto; display: block;" />'
        else:
            logo_html = "<div style='font-size: 5rem; color: white; margin: 2rem 0;'>🏭</div>"
    except Exception as e:
        logo_html = "<div style='font-size: 5rem; color: white; margin: 2rem 0;'>🏭</div>"
    
    # Try to load and encode the Mondragón logo
    mondragon_logo_html = ""
    try:
        uni_logo = "mondragon.logo.png"
        if os.path.exists(uni_logo):
            with open(uni_logo, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode()
                mondragon_logo_html = f'<img src="data:image/png;base64,{encoded}" style="width: 300px; max-width: 80%; margin: 2rem auto 1rem auto; display: block;" />'
        else:
            # Fallback to URL
            mondragon_logo_html = '<img src="https://www.mondragon.edu/o/mu-theme/images/logo.png" style="width: 300px; max-width: 80%; margin: 2rem auto 1rem auto; display: block;" />'
    except Exception as e:
        mondragon_logo_html = "<h3 style='color: white; margin: 2rem 0 1rem 0;'>Mondragón Unibertsitatea</h3>"
    
    # Single HTML block with everything embedded
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 3rem 2rem 4rem 2rem; border-radius: 15px; text-align: center;
                box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4); margin-bottom: 3rem;'>
        {logo_html}
        <p style='color: white; font-size: 2.6rem; margin: 0.5rem 0 1rem 0; opacity: 0.95; font-weight: 500;'>
            Industrial Symbiosis Platform
        </p>
        <p style='color: white; font-size: 1.6rem; margin: 1rem 0 2rem 0; opacity: 0.9; font-weight: 300; line-height: 1.5;'>
            Optimizing Resource Exchanges for Sustainable Industrial Networks
        </p>
        <hr style='border: none; border-top: 2px solid rgba(255,255,255,0.2); margin: 2rem auto; width: 60%;' />
        {mondragon_logo_html}
        <p style='color: white; font-size: 1.1rem; margin: 0.5rem 0 0 0; opacity: 0.9;'>
            Powered by <strong>Mondragón Unibertsitatea</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Introduction
    st.markdown("""
    <div style='text-align: center; max-width: 900px; margin: 0 auto 3rem auto;'>
        <h2 style='color: #667eea; margin-bottom: 1rem;'>What is Industrial Symbiosis?</h2>
        <p style='font-size: 1.15rem; line-height: 1.8; color: #333;'>
            <strong>Industrial symbiosis</strong> is a collaborative strategy where different companies 
            exchange resources (waste, energy, materials) to create economic and environmental value.
            This platform uses <strong>advanced mathematical optimization (MILP)</strong> and 
            <strong>Monte Carlo simulation</strong> to design optimal exchange networks considering 
            costs, distances, and uncertainty.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Features
    st.markdown("""
    <h2 style='text-align: center; color: #667eea; margin: 3rem 0 2rem 0;'>✨ Key Features</h2>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%); 
                    padding: 2rem; border-radius: 12px; height: 100%; text-align: center;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>🏢</div>
            <h3 style='color: white; margin-bottom: 1rem;'>Firm Management</h3>
            <p style='color: white; opacity: 0.95; font-size: 0.95rem;'>
                Configure up to 5 firms with their geographic locations, 
                available resources (heat, scrap) and needs (electricity, polymers)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                    padding: 2rem; border-radius: 12px; height: 100%; text-align: center;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>⚙️</div>
            <h3 style='color: white; margin-bottom: 1rem;'>MILP Optimization</h3>
            <p style='color: white; opacity: 0.95; font-size: 0.95rem;'>
                Find the optimal exchange network minimizing total costs 
                (procurement, disposal, recovery, transport, activation)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #2196F3 0%, #00BCD4 100%); 
                    padding: 2rem; border-radius: 12px; height: 100%; text-align: center;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>📊</div>
            <h3 style='color: white; margin-bottom: 1rem;'>Monte Carlo</h3>
            <p style='color: white; opacity: 0.95; font-size: 0.95rem;'>
                Simulate hundreds of scenarios with supply/demand variations 
                to identify robust solutions under uncertainty
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 3rem 0;'></div>", unsafe_allow_html=True)
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 12px; height: 100%; text-align: center;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>🌐</div>
            <h3 style='color: white; margin-bottom: 1rem;'>Interactive Maps</h3>
            <p style='color: white; opacity: 0.95; font-size: 0.95rem;'>
                Visualize the symbiosis network with geographic maps, 
                connections between firms and resource flows
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #F093FB 0%, #F5576C 100%); 
                    padding: 2rem; border-radius: 12px; height: 100%; text-align: center;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>💰</div>
            <h3 style='color: white; margin-bottom: 1rem;'>Cost Analysis</h3>
            <p style='color: white; opacity: 0.95; font-size: 0.95rem;'>
                Configure detailed economic parameters and analyze 
                cost breakdown by component (transport, processing, etc.)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #FA8BFF 0%, #2BD2FF 90%, #2BFF88 100%); 
                    padding: 2rem; border-radius: 12px; height: 100%; text-align: center;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>📈</div>
            <h3 style='color: white; margin-bottom: 1rem;'>Statistical Analysis</h3>
            <p style='color: white; opacity: 0.95; font-size: 0.95rem;'>
                Cost distributions, robustness metrics, 
                sensitivity analysis and AI-based recommendations
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Workflow Overview
    st.markdown("""
    <h2 style='text-align: center; color: #667eea; margin: 4rem 0 2rem 0;'>🔄 Workflow</h2>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='display: flex; justify-content: space-around; align-items: center; margin: 2rem 0;'>
        <div style='text-align: center;'>
            <div style='background: #4CAF50; color: white; border-radius: 50%; width: 70px; height: 70px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 28px; font-weight: bold;'>
                1
            </div>
            <p style='margin-top: 1rem; font-weight: bold; font-size: 1.1rem;'>Configure Firms</p>
            <p style='font-size: 0.9rem; color: #666;'>Locations and S/D data</p>
        </div>
        <div style='font-size: 40px; color: #999;'>→</div>
        <div style='text-align: center;'>
            <div style='background: #2196F3; color: white; border-radius: 50%; width: 70px; height: 70px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 28px; font-weight: bold;'>
                2
            </div>
            <p style='margin-top: 1rem; font-weight: bold; font-size: 1.1rem;'>Matrices & Synergies</p>
            <p style='font-size: 0.9rem; color: #666;'>Define recovery γ and δ</p>
        </div>
        <div style='font-size: 40px; color: #999;'>→</div>
        <div style='text-align: center;'>
            <div style='background: #FF9800; color: white; border-radius: 50%; width: 70px; height: 70px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 28px; font-weight: bold;'>
                3
            </div>
            <p style='margin-top: 1rem; font-weight: bold; font-size: 1.1rem;'>Optimize</p>
            <p style='font-size: 0.9rem; color: #666;'>Run Monte Carlo + MILP</p>
        </div>
        <div style='font-size: 40px; color: #999;'>→</div>
        <div style='text-align: center;'>
            <div style='background: #9C27B0; color: white; border-radius: 50%; width: 70px; height: 70px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 28px; font-weight: bold;'>
                4
            </div>
            <p style='margin-top: 1rem; font-weight: bold; font-size: 1.1rem;'>Visualize Results</p>
            <p style='font-size: 0.9rem; color: #666;'>Maps, statistics, networks</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Call to Action
    st.markdown("<div style='margin: 4rem 0 2rem 0;'></div>", unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        st.markdown("""
        <style>
        div.stButton > button {
            font-size: 4.5rem !important;
            padding: 3rem 5rem !important;
            font-weight: 900 !important;
            border-radius: 20px !important;
            height: auto !important;
        }
        </style>
        """, unsafe_allow_html=True)
        if st.button("🚀 Start Using the Platform", type="primary", width='stretch'):
            st.session_state.show_landing = False
            st.rerun()
    
    # Footer Information
    st.markdown("""
    <div style='margin-top: 4rem; padding: 2rem; background: #f8f9fa; border-radius: 10px; text-align: center;'>
        <h3 style='color: #667eea; margin-bottom: 1rem;'>📚 Additional Resources</h3>
        <p style='color: #666; font-size: 0.95rem; line-height: 1.6;'>
            For more information about industrial symbiosis, check the <strong>📖 User Guide</strong> tab 
            once inside the platform. There you will find complete documentation, use cases, 
            technical glossary and frequently asked questions.
        </p>
        <p style='margin-top: 1.5rem; color: #999; font-size: 0.85rem;'>
            © 2026 Mondragón Unibertsitatea | SIMBIOPTIMIZE v1.0
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()  # Stop execution here to show only landing page

# ============================================
# SIDEBAR - BACK TO LANDING
# ============================================
with st.sidebar:
    st.markdown("---")
    if st.button("🏠 Volver a la Portada", width='stretch'):
        st.session_state.show_landing = True
        st.rerun()
    st.markdown("---")

# ============================================
# MAIN HEADER (shown after landing page)
# ============================================
# Load platform logo for header
import os
import base64

header_logo_html = ""
try:
    platform_logo = "LogoSymbiosis.jpg"
    if os.path.exists(platform_logo):
        with open(platform_logo, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            header_logo_html = f'<img src="data:image/jpeg;base64,{encoded}" style="height: 80px; margin-bottom: 1rem; display: block; margin-left: auto; margin-right: auto;" />'
    else:
        header_logo_html = "<div style='font-size: 3rem; margin-bottom: 1rem;'>🏭</div>"
except:
    header_logo_html = "<div style='font-size: 3rem; margin-bottom: 1rem;'>🏭</div>"

st.markdown(f"""
<div class="main-header">
    {header_logo_html}
    <div style="font-size: 2rem; font-weight: 500; margin-bottom: 0.5rem; opacity: 0.95;">Industrial Symbiosis Platform</div>
    <div class="main-subtitle" style="font-size: 1.4rem;">Optimizing Resource Exchanges for Sustainable Industrial Networks</div>
    <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.85;">Powered by Mondragón Unibertsitatea</div>
</div>
""", unsafe_allow_html=True)

# ============================================
# INITIALIZE SESSION STATE (continued)
# ============================================
if "firm_locations" not in st.session_state:
    st.session_state.firm_locations = {
        "F1": {"name": "Firm 1", "lat": 40.416775, "lon": -3.703790},
        "F2": {"name": "Firm 2", "lat": 40.426775, "lon": -3.713790},
        "F3": {"name": "Firm 3", "lat": 40.406775, "lon": -3.693790},
        "F4": {"name": "Firm 4", "lat": 40.436775, "lon": -3.723790},
        "F5": {"name": "Firm 5", "lat": 40.396775, "lon": -3.683790},
    }

if "cost_params" not in st.session_state:
    st.session_state.cost_params = DEFAULT_COST_PARAMS.copy()

# Initialize data source tracking (True = use real data, False = use EIO)
if "use_real_data" not in st.session_state:
    st.session_state.use_real_data = {
        "F1": False,
        "F2": False,
        "F3": False,
        "F4": False,
        "F5": False,
    }

# Initialize firm data in session state
if "firm_supply" not in st.session_state:
    st.session_state.firm_supply = {
        "F1": {"Heat": 100.0, "Scrap": 50.0, "Steam": 30.0},
        "F2": {"Heat": 80.0, "Scrap": 60.0, "Steam": 25.0},
        "F3": {"Heat": 120.0, "Scrap": 40.0, "Steam": 35.0},
        "F4": {"Heat": 90.0, "Scrap": 70.0, "Steam": 28.0},
        "F5": {"Heat": 110.0, "Scrap": 55.0, "Steam": 32.0},
    }

if "firm_demand" not in st.session_state:
    st.session_state.firm_demand = {
        "F1": {"Electricity": 90.0, "Water": 20.0, "Polymer": 45.0},
        "F2": {"Electricity": 70.0, "Water": 25.0, "Polymer": 55.0},
        "F3": {"Electricity": 100.0, "Water": 18.0, "Polymer": 35.0},
        "F4": {"Electricity": 80.0, "Water": 22.0, "Polymer": 65.0},
        "F5": {"Electricity": 95.0, "Water": 24.0, "Polymer": 50.0},
    }

# ============================================
# CREATE MAIN TABS
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏢 Firms Management",
    "📊 Data Matrices",
    "⚙️ Optimization",
    "🌐 Network Visualization",
    "📖 User Guide"
])

# ============================================
# TAB 1: FIRMS MANAGEMENT (Individual Firm Cards)
# ============================================
with tab1:
    # Create sub-tabs for each firm
    firm_tabs = st.tabs([f"🏭 Firm {i}" for i in range(1, 6)])
    
    for idx, firm_tab in enumerate(firm_tabs):
        firm_id = f"F{idx+1}"
        
        with firm_tab:
            st.markdown(f'<div class="firm-card">', unsafe_allow_html=True)
            st.markdown(f"### Configuration for Firm {idx+1}")
            
            # Data source toggle
            col_toggle, col_indicator = st.columns([3, 1])
            with col_toggle:
                use_real = st.checkbox(
                    "📊 Use Real Data (override EIO estimates)",
                    value=st.session_state.use_real_data[firm_id],
                    key=f"toggle_real_{firm_id}",
                    help="Check this box to enter real data. Uncheck to use EIO model estimates."
                )
                st.session_state.use_real_data[firm_id] = use_real
            
            with col_indicator:
                if use_real:
                    st.success("📊 REAL")
                else:
                    st.info("🔢 EIO")
            
            st.markdown("---")
            
            # Basic Information Section
            st.markdown("#### 📋 Basic Information")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                name = st.text_input(
                    "Firm Name",
                    value=st.session_state.firm_locations[firm_id]["name"],
                    key=f"name_{firm_id}",
                    help="Enter the official name of the company"
                )
                st.session_state.firm_locations[firm_id]["name"] = name
            
            with col2:
                industry_type = st.selectbox(
                    "Industry Type",
                    ["Manufacturing", "Energy", "Chemical", "Recycling", "Other"],
                    key=f"industry_{firm_id}"
                )
            
            st.markdown("---")
            
            # Geographic Coordinates Section
            st.markdown("#### 📍 Geographic Location")
            st.caption("Enter precise coordinates for accurate distance calculations")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                lat = st.number_input(
                    "Latitude",
                    value=st.session_state.firm_locations[firm_id]["lat"],
                    format="%.6f",
                    key=f"lat_{firm_id}",
                    help="Latitude in decimal degrees (e.g., 40.416775)"
                )
                st.session_state.firm_locations[firm_id]["lat"] = lat
            
            with col2:
                lon = st.number_input(
                    "Longitude",
                    value=st.session_state.firm_locations[firm_id]["lon"],
                    format="%.6f",
                    key=f"lon_{firm_id}",
                    help="Longitude in decimal degrees (e.g., -3.703790)"
                )
                st.session_state.firm_locations[firm_id]["lon"] = lon
            
            with col3:
                st.metric("Current Position", f"{lat:.4f}, {lon:.4f}")
            
            st.markdown("---")
            
            # Supply Data Section
            st.markdown("#### 📤 Supply Data (Resources Available)")
            if use_real:
                st.caption("✏️ Enter actual production/waste quantities (units/month)")
            else:
                st.caption("🔢 Values calculated from EIO model (read-only)")
            
            # Get EIO values for this firm (use Water from EIO as steam/wastewater proxy)
            eio_heat = df_S_il_eoi.loc[firm_id, "Waste heat"]
            eio_scrap = df_S_il_eoi.loc[firm_id, "Plastic scrap"]
            # Note: EIO doesn't have steam/wastewater in waste matrix, using default
            eio_steam = 30.0  # Default value as EIO doesn't track this waste type
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if use_real:
                    heat_supply = st.number_input(
                        "Heat Available (MWh/month)",
                        value=st.session_state.firm_supply[firm_id]["Heat"],
                        min_value=0.0,
                        format="%.2f",
                        key=f"heat_supply_{firm_id}"
                    )
                    st.session_state.firm_supply[firm_id]["Heat"] = heat_supply
                else:
                    st.number_input(
                        "Heat Available (MWh/month)",
                        value=eio_heat,
                        min_value=0.0,
                        format="%.2f",
                        key=f"heat_supply_{firm_id}",
                        disabled=True
                    )
                    heat_supply = eio_heat
                    st.session_state.firm_supply[firm_id]["Heat"] = eio_heat
            
            with col2:
                if use_real:
                    scrap_supply = st.number_input(
                        "Scrap Materials Available (tons/month)",
                        value=st.session_state.firm_supply[firm_id]["Scrap"],
                        min_value=0.0,
                        format="%.2f",
                        key=f"scrap_supply_{firm_id}"
                    )
                    st.session_state.firm_supply[firm_id]["Scrap"] = scrap_supply
                else:
                    st.number_input(
                        "Scrap Materials Available (tons/month)",
                        value=eio_scrap,
                        min_value=0.0,
                        format="%.2f",
                        key=f"scrap_supply_{firm_id}",
                        disabled=True
                    )
                    scrap_supply = eio_scrap
                    st.session_state.firm_supply[firm_id]["Scrap"] = eio_scrap
            
            with col3:
                if use_real:
                    steam_supply = st.number_input(
                        "Steam/Wastewater Available (m³/month)",
                        value=st.session_state.firm_supply[firm_id].get("Steam", 30.0),
                        min_value=0.0,
                        format="%.2f",
                        key=f"steam_supply_{firm_id}"
                    )
                    st.session_state.firm_supply[firm_id]["Steam"] = steam_supply
                else:
                    st.number_input(
                        "Steam/Wastewater Available (m³/month)",
                        value=eio_steam,
                        min_value=0.0,
                        format="%.2f",
                        key=f"steam_supply_{firm_id}",
                        disabled=True
                    )
                    steam_supply = eio_steam
                    st.session_state.firm_supply[firm_id]["Steam"] = eio_steam
            
            st.markdown("---")
            
            # Demand Data Section
            st.markdown("#### 📥 Demand Data (Resources Needed)")
            if use_real:
                st.caption("✏️ Enter actual consumption/requirements (units/month)")
            else:
                st.caption("🔢 Values calculated from EIO model (read-only)")
            
            # Get EIO values for this firm
            eio_elec = df_D_jk_eoi.loc[firm_id, "Electricity"]
            eio_water = df_D_jk_eoi.loc[firm_id, "Water"]
            eio_polymer = df_D_jk_eoi.loc[firm_id, "Virgin polymer"]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if use_real:
                    elec_demand = st.number_input(
                        "Electricity Needed (MWh/month)",
                        value=st.session_state.firm_demand[firm_id]["Electricity"],
                        min_value=0.0,
                        format="%.2f",
                        key=f"elec_demand_{firm_id}"
                    )
                    st.session_state.firm_demand[firm_id]["Electricity"] = elec_demand
                else:
                    st.number_input(
                        "Electricity Needed (MWh/month)",
                        value=eio_elec,
                        min_value=0.0,
                        format="%.2f",
                        key=f"elec_demand_{firm_id}",
                        disabled=True
                    )
                    elec_demand = eio_elec
                    st.session_state.firm_demand[firm_id]["Electricity"] = eio_elec
            
            with col2:
                if use_real:
                    water_demand = st.number_input(
                        "Water Needed (m³/month)",
                        value=st.session_state.firm_demand[firm_id].get("Water", 20.0),
                        min_value=0.0,
                        format="%.2f",
                        key=f"water_demand_{firm_id}"
                    )
                    st.session_state.firm_demand[firm_id]["Water"] = water_demand
                else:
                    st.number_input(
                        "Water Needed (m³/month)",
                        value=eio_water,
                        min_value=0.0,
                        format="%.2f",
                        key=f"water_demand_{firm_id}",
                        disabled=True
                    )
                    water_demand = eio_water
                    st.session_state.firm_demand[firm_id]["Water"] = eio_water
            
            with col3:
                if use_real:
                    polymer_demand = st.number_input(
                        "Polymer Materials Needed (tons/month)",
                        value=st.session_state.firm_demand[firm_id]["Polymer"],
                        min_value=0.0,
                        format="%.2f",
                        key=f"polymer_demand_{firm_id}"
                    )
                    st.session_state.firm_demand[firm_id]["Polymer"] = polymer_demand
                else:
                    st.number_input(
                        "Polymer Materials Needed (tons/month)",
                        value=eio_polymer,
                        min_value=0.0,
                        format="%.2f",
                        key=f"polymer_demand_{firm_id}",
                        disabled=True
                    )
                    polymer_demand = eio_polymer
                    st.session_state.firm_demand[firm_id]["Polymer"] = eio_polymer
            
            st.markdown("---")
            
            # Summary for this firm
            st.markdown("#### 📊 Firm Summary")
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric("Heat Supply", f"{heat_supply:.1f} MWh")
            with col2:
                st.metric("Scrap Supply", f"{scrap_supply:.1f} tons")
            with col3:
                st.metric("Steam Supply", f"{steam_supply:.1f} m³")
            with col4:
                st.metric("Electricity Demand", f"{elec_demand:.1f} MWh")
            with col5:
                st.metric("Water Demand", f"{water_demand:.1f} m³")
            with col6:
                st.metric("Polymer Demand", f"{polymer_demand:.1f} tons")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary of all firms
    st.markdown("---")
    st.markdown("### 📊 Network Overview")
    
    # Data source summary
    st.markdown("#### 🔍 Data Source Summary")
    col1, col2, col3 = st.columns(3)
    
    real_count = sum(st.session_state.use_real_data.values())
    eio_count = 5 - real_count
    
    with col1:
        st.metric("📊 Real Data", f"{real_count}/5 firms")
    with col2:
        st.metric("🔢 EIO Estimates", f"{eio_count}/5 firms")
    with col3:
        if real_count == 0:
            st.info("🔢 Full EIO Mode")
        elif real_count == 5:
            st.success("📊 Full Real Data")
        else:
            st.warning("🔀 Hybrid Mode")
    
    # Detailed summary table
    summary_data = []
    for firm_id in ["F1", "F2", "F3", "F4", "F5"]:
        data_source = "📊 Real" if st.session_state.use_real_data[firm_id] else "🔢 EIO"
        summary_data.append({
            "Firm": st.session_state.firm_locations[firm_id]["name"],
            "Data Source": data_source,
            "Latitude": f"{st.session_state.firm_locations[firm_id]['lat']:.6f}",
            "Longitude": f"{st.session_state.firm_locations[firm_id]['lon']:.6f}",
            "Heat Supply": st.session_state.firm_supply[firm_id]["Heat"],
            "Scrap Supply": st.session_state.firm_supply[firm_id]["Scrap"],
            "Steam Supply": st.session_state.firm_supply[firm_id].get("Steam", 0.0),
            "Electricity Demand": st.session_state.firm_demand[firm_id]["Electricity"],
            "Water Demand": st.session_state.firm_demand[firm_id].get("Water", 0.0),
            "Polymer Demand": st.session_state.firm_demand[firm_id]["Polymer"],
        })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, width='stretch', hide_index=True)

# ============================================
# TAB 2: DATA MATRICES VIEW
# ============================================
with tab2:
    st.markdown("### 📊 Supply & Demand Matrices")
    st.markdown("Visual overview of all firms' supply and demand data")
    
    # Build matrices from session state
    supply_data = []
    demand_data = []
    
    for firm_id in ["F1", "F2", "F3", "F4", "F5"]:
        supply_data.append([
            st.session_state.firm_supply[firm_id]["Heat"],
            st.session_state.firm_supply[firm_id]["Scrap"],
            st.session_state.firm_supply[firm_id].get("Steam", 0.0)
        ])
        demand_data.append([
            st.session_state.firm_demand[firm_id]["Electricity"],
            st.session_state.firm_demand[firm_id].get("Water", 0.0),
            st.session_state.firm_demand[firm_id]["Polymer"]
        ])
    
    # Create DataFrames
    df_supply = pd.DataFrame(
        supply_data,
        columns=['Heat (MWh)', 'Scrap (tons)', 'Steam (m³)'],
        index=[st.session_state.firm_locations[f]["name"] for f in ["F1", "F2", "F3", "F4", "F5"]]
    )
    
    df_demand = pd.DataFrame(
        demand_data,
        columns=['Electricity (MWh)', 'Water (m³)', 'Polymer (tons)'],
        index=[st.session_state.firm_locations[f]["name"] for f in ["F1", "F2", "F3", "F4", "F5"]]
    )
    
    # Store in session state for optimization
    st.session_state.S_il = pd.DataFrame(supply_data, columns=['Heat', 'Scrap', 'Steam'], index=['F1', 'F2', 'F3', 'F4', 'F5'])
    st.session_state.D_jk = pd.DataFrame(demand_data, columns=['Electricity', 'Water', 'Polymer'], index=['F1', 'F2', 'F3', 'F4', 'F5'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📤 Supply Matrix (S<sub>il</sub>)", unsafe_allow_html=True)
        st.markdown("Resources each firm can provide")
        st.dataframe(df_supply, width='stretch')
        
        # Total supply
        st.markdown("**Total Network Supply:**")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Heat", f"{df_supply['Heat (MWh)'].sum():.1f} MWh")
        with col_b:
            st.metric("Total Scrap", f"{df_supply['Scrap (tons)'].sum():.1f} tons")
        with col_c:
            st.metric("Total Steam", f"{df_supply['Steam (m³)'].sum():.1f} m³")
    
    with col2:
        st.markdown("#### 📥 Demand Matrix (D<sub>jk</sub>)", unsafe_allow_html=True)
        st.markdown("Resources each firm requires")
        st.dataframe(df_demand, width='stretch')
        
        # Total demand
        st.markdown("**Total Network Demand:**")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Electricity", f"{df_demand['Electricity (MWh)'].sum():.1f} MWh")
        with col_b:
            st.metric("Total Water", f"{df_demand['Water (m³)'].sum():.1f} m³")
        with col_c:
            st.metric("Total Polymer", f"{df_demand['Polymer (tons)'].sum():.1f} tons")
    
    st.markdown("---")
    
    # Synergy Selection Matrix
    st.markdown("### 🔄 Synergy Configuration")
    st.markdown("Select which waste-to-input transformations are technically feasible")
    st.caption("Only enabled synergies (✓) will be considered during optimization")
    
    # Define wastes and inputs
    wastes = ["Waste heat", "Plastic scrap", "Steam/Wastewater"]
    inputs = ["Electricity", "Water", "Polymer"]
    
    # Initialize synergy matrix if not exists
    if "synergy_matrix" not in st.session_state:
        # Create empty matrix (all False)
        st.session_state.synergy_matrix = pd.DataFrame(
            False, 
            index=wastes, 
            columns=inputs
        )
    
    # Interactive synergy matrix editor
    st.markdown("#### Feasibility Matrix")
    st.caption("Check the boxes for technically viable transformations")
    
    edited_matrix = st.data_editor(
        st.session_state.synergy_matrix,
        width='stretch',
        hide_index=False,
        column_config={
            col: st.column_config.CheckboxColumn(
                col,
                help=f"Can waste be converted to {col}?",
                default=False,
            )
            for col in inputs
        }
    )
    
    # Update session state
    st.session_state.synergy_matrix = edited_matrix
    
    # Summary of active synergies
    active_count = edited_matrix.sum().sum()
    if active_count == 0:
        st.error("⚠️ No synergies selected! Please enable at least one transformation.")
    else:
        st.info(f"✅ {int(active_count)} synergy pathway(s) enabled for optimization")
        
        # Show active synergies list
        with st.expander("📋 View Active Synergies"):
            for waste in wastes:
                for input_type in inputs:
                    if edited_matrix.loc[waste, input_type]:
                        st.write(f"✓ {waste} → {input_type}")
    
    st.markdown("---")
    
    # Network Balance Analysis
    st.markdown("### ⚖️ Network Balance Analysis")
    st.caption("Comparing total supply vs demand (after transformation) - Only showing enabled synergies")
    
    # Get synergy matrix
    synergy_matrix = st.session_state.get("synergy_matrix")
    
    # Check which synergies are enabled
    heat_to_elec_enabled = synergy_matrix.loc["Waste heat", "Electricity"] if synergy_matrix is not None else False
    steam_to_water_enabled = synergy_matrix.loc["Steam/Wastewater", "Water"] if synergy_matrix is not None else False
    scrap_to_poly_enabled = synergy_matrix.loc["Plastic scrap", "Polymer"] if synergy_matrix is not None else False
    
    # Count enabled synergies
    enabled_count = int(sum([heat_to_elec_enabled, steam_to_water_enabled, scrap_to_poly_enabled]))
    
    if enabled_count == 0:
        st.warning("⚠️ No synergies enabled. Please select at least one transformation in the Synergy Configuration section above.")
    else:
        # Show recovery rate AND substitution share sliders for enabled synergies
        st.markdown("#### ⚗️ Conversion Parameters")
        st.caption("Configure efficiency (γ) and maximum substitution rate (δ) for each enabled synergy")
        
        # Explanation of delta parameter
        with st.expander("ℹ️ What is Maximum Substitution Rate (δ)?"):
            st.markdown("""
            **Maximum Substitution Rate (δ)** limits how much of an input demand can be satisfied by waste-derived resources.
            
            **Why δ < 100%?**
            - 🏛️ **Regulatory**: Environmental regulations may limit recycled content
            - 🔒 **Safety**: Critical systems require virgin material guarantees
            - 🔧 **Technical**: Product specifications may require minimum virgin content
            - 📊 **Reliability**: Diversification to avoid supply disruption
            
            **Example:** If δ = 80% for electricity:
            - Maximum 80% of electricity can come from waste heat
            - Minimum 20% must be from conventional grid
            
            **Constraint enforced:** $r_{lk} \\times \\sum_i q_{ij}^{lk} \\leq \\delta_{lk} \\times D_j^k$
            """)
        
        # Create columns for each enabled synergy
        slider_cols = []
        if heat_to_elec_enabled:
            slider_cols.append("heat_elec")
        if steam_to_water_enabled:
            slider_cols.append("steam_water")
        if scrap_to_poly_enabled:
            slider_cols.append("scrap_poly")
        
        cols_sliders = st.columns(len(slider_cols))
        
        # Initialize default values
        r11 = 0.9
        delta_heat_elec = 0.8
        r_steam_water = 0.85
        delta_steam_water = 0.8
        r23 = 0.8
        delta_scrap_poly = 0.8
        
        for idx, col_type in enumerate(slider_cols):
            with cols_sliders[idx]:
                if col_type == "heat_elec":
                    st.markdown("**🔥 Heat → Electricity**")
                    r11 = st.slider(
                        "Recovery Rate (γ)", 
                        0.5, 1.0, 0.9, 0.05, 
                        key="r11_matrix",
                        help="Efficiency of converting waste heat to electricity"
                    )
                    st.caption(f"1 MWh heat → {r11:.2f} MWh electricity")
                    
                    delta_heat_elec = st.slider(
                        "Max Substitution (δ)", 
                        0.0, 1.0, 0.8, 0.05, 
                        key="delta_heat_elec_matrix",
                        help="Maximum % of electricity demand that can come from waste heat"
                    )
                    st.caption(f"Max {delta_heat_elec*100:.0f}% from waste, {(1-delta_heat_elec)*100:.0f}% virgin required")
                    
                elif col_type == "steam_water":
                    st.markdown("**💧 Steam → Water**")
                    r_steam_water = st.slider(
                        "Recovery Rate (γ)", 
                        0.5, 1.0, 0.85, 0.05, 
                        key="r_steam_water_matrix",
                        help="Efficiency of treating wastewater/steam to clean water"
                    )
                    st.caption(f"1 m³ steam → {r_steam_water:.2f} m³ water")
                    
                    delta_steam_water = st.slider(
                        "Max Substitution (δ)", 
                        0.0, 1.0, 0.8, 0.05, 
                        key="delta_steam_water_matrix",
                        help="Maximum % of water demand that can come from treated steam"
                    )
                    st.caption(f"Max {delta_steam_water*100:.0f}% from waste, {(1-delta_steam_water)*100:.0f}% virgin required")
                    
                elif col_type == "scrap_poly":
                    st.markdown("**♻️ Scrap → Polymer**")
                    r23 = st.slider(
                        "Recovery Rate (γ)", 
                        0.5, 1.0, 0.8, 0.05, 
                        key="r23_matrix",
                        help="Efficiency of recycling plastic scrap to virgin-quality polymer"
                    )
                    st.caption(f"1 ton scrap → {r23:.2f} ton polymer")
                    
                    delta_scrap_poly = st.slider(
                        "Max Substitution (δ)", 
                        0.0, 1.0, 0.8, 0.05, 
                        key="delta_scrap_poly_matrix",
                        help="Maximum % of polymer demand that can come from recycled scrap"
                    )
                    st.caption(f"Max {delta_scrap_poly*100:.0f}% from waste, {(1-delta_scrap_poly)*100:.0f}% virgin required")
        
        st.markdown("---")
        st.markdown("#### 📊 Balance Analysis Results")
        
        # Create dynamic columns based on enabled synergies
        balance_cols = st.columns(enabled_count)
        col_idx = 0
        
        # Heat → Electricity
        if heat_to_elec_enabled:
            with balance_cols[col_idx]:
                st.markdown("**🔥 Electricity Balance**")
                potential_elec = df_supply['Heat (MWh)'].sum() * r11
                elec_demand = df_demand['Electricity (MWh)'].sum()
                delta_heat_elec = st.session_state.get("delta_heat_elec_matrix", 1.0)
                max_heat_substitution = elec_demand * delta_heat_elec
                actual_heat_used = min(potential_elec, max_heat_substitution)
                virgin_elec_needed = elec_demand - actual_heat_used
                st.metric(
                    "Heat Used",
                    f"{actual_heat_used:.1f} MWh",
                    f"{actual_heat_used/elec_demand*100:.0f}% of demand"
                )
                st.metric(
                    "Virgin Electricity Needed",
                    f"{virgin_elec_needed:.1f} MWh",
                    f"{virgin_elec_needed/elec_demand*100:.0f}% of demand"
                )
                balance_elec = actual_heat_used - elec_demand
                if balance_elec >= 0:
                    st.success("✅ Heat covers demand")
                else:
                    st.warning("⚠️ Virgin electricity required")
            col_idx += 1
        
        # Steam → Water
        if steam_to_water_enabled:
            with balance_cols[col_idx]:
                st.markdown("**💧 Water Balance**")
                potential_water = df_supply['Steam (m³)'].sum() * r_steam_water
                balance_water = potential_water - df_demand['Water (m³)'].sum()
                st.metric(
                    "Potential Supply",
                    f"{potential_water:.1f} m³",
                    f"{balance_water:+.1f} m³ vs Demand"
                )
                if balance_water >= 0:
                    st.success("✅ Surplus")
                else:
                    st.warning("⚠️ Deficit")
            col_idx += 1
        
        # Scrap → Polymer
        if scrap_to_poly_enabled:
            with balance_cols[col_idx]:
                st.markdown("**♻️ Polymer Balance**")
                potential_polymer = df_supply['Scrap (tons)'].sum() * r23
                polymer_demand = df_demand['Polymer (tons)'].sum()
                delta_scrap_poly = st.session_state.get("delta_scrap_poly_matrix", 1.0)
                max_scrap_substitution = polymer_demand * delta_scrap_poly
                actual_scrap_used = min(potential_polymer, max_scrap_substitution)
                virgin_polymer_needed = polymer_demand - actual_scrap_used
                st.metric(
                    "Scrap Used",
                    f"{actual_scrap_used:.1f} tons",
                    f"{actual_scrap_used/polymer_demand*100:.0f}% of demand"
                )
                st.metric(
                    "Virgin Polymer Needed",
                    f"{virgin_polymer_needed:.1f} tons",
                    f"{virgin_polymer_needed/polymer_demand*100:.0f}% of demand"
                )
                balance_polymer = actual_scrap_used - polymer_demand
                if balance_polymer >= 0:
                    st.success("✅ Scrap covers demand")
                else:
                    st.warning("⚠️ Virgin polymer required")
    
    # Visualization
    st.markdown("---")
    st.markdown("### 📈 Visual Comparison")
    
    comparison_data = pd.DataFrame({
        'Metric': ['Heat/Electricity', 'Heat/Electricity', 'Scrap/Polymer', 'Scrap/Polymer'],
        'Type': ['Supply', 'Demand', 'Supply', 'Demand'],
        'Value': [
            df_supply['Heat (MWh)'].sum(),
            df_demand['Electricity (MWh)'].sum(),
            df_supply['Scrap (tons)'].sum(),
            df_demand['Polymer (tons)'].sum()
        ]
    })
    
    st.bar_chart(comparison_data.pivot(index='Metric', columns='Type', values='Value'))
# ============================================
# TAB 3: OPTIMIZATION ENGINE
# ============================================
with tab3:
    # Professional Header
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h2 style='color: white; margin: 0;'>⚙️ Industrial Symbiosis Optimization Engine</h2>
        <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>
            Advanced Monte Carlo simulation with MILP optimization for optimal resource exchange networks
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Get matrices from session state
    df_S_il = st.session_state.get("S_il")
    df_D_jk = st.session_state.get("D_jk")
    
    if df_S_il is None or df_D_jk is None:
        st.warning("⚠️ Please configure firm data first in 'Firms Management' tab")
        st.stop()

    # Two-Phase Process Indicator
    st.markdown("""
    <div style='display: flex; justify-content: space-around; margin: 2rem 0;'>
        <div style='text-align: center;'>
            <div style='background: #4CAF50; color: white; border-radius: 50%; width: 60px; height: 60px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 24px;'>
                1
            </div>
            <p style='margin-top: 0.5rem; font-weight: bold;'>Generate Scenarios</p>
            <p style='font-size: 0.85rem; color: #666;'>Create (S,D) pairs</p>
        </div>
        <div style='text-align: center; align-self: center; font-size: 30px; color: #999;'>
            →
        </div>
        <div style='text-align: center;'>
            <div style='background: #2196F3; color: white; border-radius: 50%; width: 60px; height: 60px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 24px;'>
                2
            </div>
            <p style='margin-top: 0.5rem; font-weight: bold;'>Optimize Each Scenario</p>
            <p style='font-size: 0.85rem; color: #666;'>Find optimal q & z</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎛️ Configuration Parameters")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        n_sim_combo = st.number_input(
            "🎲 Number of Scenarios",
            min_value=10, max_value=1000, value=100, step=10,
            key="n_sim_combo",
            help="More scenarios = better statistical robustness"
        )
    with col2:
        variation_pct_combo = st.slider(
            "📊 Uncertainty (±%)",
            min_value=1, max_value=50, value=10, step=1,
            key="var_pct_combo",
            help="Variation in supply/demand data"
        )
    with col3:
        distribution_combo = st.selectbox(
            "📈 Distribution",
            ["uniform", "normal"],
            key="dist_type_combo",
            help="Statistical distribution type"
        )
    with col4:
        st.metric("Total Scenarios", f"{n_sim_combo:,}", "to optimize")

    st.markdown("---")
    
    # Cost Parameters Configuration
    st.markdown("### 💰 Cost Parameters Configuration")
    st.markdown("Adjust economic parameters for the optimization objective function")
    
    with st.expander("ℹ️ Understanding the Cost Model", expanded=False):
        st.markdown("""
        **Objective Function Components:**
        
        $$
        \\min \\quad C_{\\text{total}} = C_{\\text{virgin}} + C_{\\text{disposal}} + C_{\\text{recovery}} + C_{\\text{activation}} + C_{\\text{transport}}
        $$
        
        **1. Virgin Input Costs ($C_{\\text{virgin}}$):**
        - Cost of purchasing virgin electricity and polymer from external suppliers
        - Higher values → optimizer prefers waste recovery over virgin inputs
        
        **2. Disposal Costs ($C_{\\text{disposal}}$):**
        - Cost of disposing unused waste heat and scrap
        - Higher values → optimizer prefers using waste instead of disposing it
        
        **3. Recovery Costs ($C_{\\text{recovery}}$):**
        - Operational cost of converting waste to useful inputs
        - Includes energy, labor, maintenance for recovery processes
        
        **4. Activation Costs ($C_{\\text{activation}}$):**
        - One-time fixed cost to establish each partnership connection
        - Creates infrastructure, contracts, monitoring systems
        - Higher values → fewer partnerships, more concentrated exchanges
        
        **5. Transport Costs ($C_{\\text{transport}}$):**
        - Variable cost proportional to quantity × distance
        - Higher values → optimizer prefers local partnerships
        """)
    
    # Create tabs for different cost categories
    cost_tab1, cost_tab2, cost_tab3, cost_tab4, cost_tab5 = st.tabs([
        "🗑️ Disposal", 
        "🏭 Virgin Inputs", 
        "♻️ Recovery", 
        "🔗 Activation", 
        "🚚 Transport"
    ])
    
    with cost_tab1:
        st.markdown("**Waste Disposal Costs**")
        st.caption("Cost of disposing waste materials if not utilized in symbiosis network")
        
        col1, col2 = st.columns(2)
        with col1:
            c_disp_heat = st.slider(
                "🔥 Heat Disposal (€/MWh)",
                min_value=COST_RANGES["C_disp_heat"][0],
                max_value=COST_RANGES["C_disp_heat"][1],
                value=st.session_state.cost_params.get("C_disp_heat", DEFAULT_COST_PARAMS["C_disp_heat"]),
                step=COST_RANGES["C_disp_heat"][2],
                key="slider_c_disp_heat",
                help="Cost to dispose of waste heat through cooling systems or flaring"
            )
            st.session_state.cost_params["C_disp_heat"] = c_disp_heat
        
        with col2:
            c_disp_scrap = st.slider(
                "♻️ Scrap Disposal (€/ton)",
                min_value=COST_RANGES["C_disp_scrap"][0],
                max_value=COST_RANGES["C_disp_scrap"][1],
                value=st.session_state.cost_params.get("C_disp_scrap", DEFAULT_COST_PARAMS["C_disp_scrap"]),
                step=COST_RANGES["C_disp_scrap"][2],
                key="slider_c_disp_scrap",
                help="Cost to dispose of plastic scrap (landfill, incineration)"
            )
            st.session_state.cost_params["C_disp_scrap"] = c_disp_scrap
        
        st.info(f"💡 **Current Total Disposal Cost Potential:** €{c_disp_heat * df_S_il['Heat'].sum() + c_disp_scrap * df_S_il['Scrap'].sum():,.0f} (if all waste disposed)")
    
    with cost_tab2:
        st.markdown("**Virgin Input Costs**")
        st.caption("Market price for purchasing virgin materials from external suppliers")
        
        col1, col2 = st.columns(2)
        with col1:
            c_vir_elec = st.slider(
                "⚡ Virgin Electricity (€/MWh)",
                min_value=COST_RANGES["C_vir_elec"][0],
                max_value=COST_RANGES["C_vir_elec"][1],
                value=st.session_state.cost_params.get("C_vir_elec", DEFAULT_COST_PARAMS["C_vir_elec"]),
                step=COST_RANGES["C_vir_elec"][2],
                key="slider_c_vir_elec",
                help="Grid electricity price (market rate)"
            )
            st.session_state.cost_params["C_vir_elec"] = c_vir_elec
        
        with col2:
            c_vir_poly = st.slider(
                "🧪 Virgin Polymer (€/ton)",
                min_value=COST_RANGES["C_vir_poly"][0],
                max_value=COST_RANGES["C_vir_poly"][1],
                value=st.session_state.cost_params.get("C_vir_poly", DEFAULT_COST_PARAMS["C_vir_poly"]),
                step=COST_RANGES["C_vir_poly"][2],
                key="slider_c_vir_poly",
                help="Virgin polymer resin market price"
            )
            st.session_state.cost_params["C_vir_poly"] = c_vir_poly
        
        st.info(f"💡 **Current Total Virgin Cost Potential:** €{c_vir_elec * df_D_jk['Electricity'].sum() + c_vir_poly * df_D_jk['Polymer'].sum():,.0f} (if all demand satisfied by virgin inputs)")
    
    with cost_tab3:
        st.markdown("**Recovery/Processing Costs**")
        st.caption("Operational costs for converting waste into useful inputs")
        
        col1, col2 = st.columns(2)
        with col1:
            c_use_heat = st.slider(
                "🔥 Heat Recovery (€/MWh)",
                min_value=COST_RANGES["C_use_heat"][0],
                max_value=COST_RANGES["C_use_heat"][1],
                value=st.session_state.cost_params.get("C_use_heat", DEFAULT_COST_PARAMS["C_use_heat"]),
                step=COST_RANGES["C_use_heat"][2],
                key="slider_c_use_heat",
                help="Cost to capture, transfer and convert waste heat to electricity"
            )
            st.session_state.cost_params["C_use_heat"] = c_use_heat
        
        with col2:
            c_use_scrap = st.slider(
                "♻️ Scrap Processing (€/ton)",
                min_value=COST_RANGES["C_use_scrap"][0],
                max_value=COST_RANGES["C_use_scrap"][1],
                value=st.session_state.cost_params.get("C_use_scrap", DEFAULT_COST_PARAMS["C_use_scrap"]),
                step=COST_RANGES["C_use_scrap"][2],
                key="slider_c_use_scrap",
                help="Cost to clean, sort, and reprocess plastic scrap into polymer"
            )
            st.session_state.cost_params["C_use_scrap"] = c_use_scrap
        
        # Show profitability gap
        gap_elec = c_vir_elec - c_use_heat
        gap_poly = c_vir_poly - c_use_scrap
        if gap_elec > 0 and gap_poly > 0:
            st.success(f"✅ **Recovery is profitable:** Electricity saves €{gap_elec:.2f}/MWh, Polymer saves €{gap_poly:.0f}/ton")
        else:
            st.warning("⚠️ **Warning:** Recovery costs higher than virgin inputs - symbiosis may not be economically attractive")

    with cost_tab4:
        st.markdown("**Partnership Activation Costs**")
        st.caption("One-time fixed investment to establish each firm-to-firm connection")
        
        col1, col2 = st.columns(2)
        with col1:
            f_heat = st.slider(
                "🔥 Heat Connection (€)",
                min_value=COST_RANGES["F_fixed_heat"][0],
                max_value=COST_RANGES["F_fixed_heat"][1],
                value=st.session_state.cost_params.get("F_fixed_heat", DEFAULT_COST_PARAMS["F_fixed_heat"]),
                step=COST_RANGES["F_fixed_heat"][2],
                key="slider_f_heat",
                help="Infrastructure cost: heat exchangers, pipes, sensors, contracts"
            )
            st.session_state.cost_params["F_fixed_heat"] = f_heat
        
        with col2:
            f_scrap = st.slider(
                "♻️ Scrap Connection (€)",
                min_value=COST_RANGES["F_fixed_scrap"][0],
                max_value=COST_RANGES["F_fixed_scrap"][1],
                value=st.session_state.cost_params.get("F_fixed_scrap", DEFAULT_COST_PARAMS["F_fixed_scrap"]),
                step=COST_RANGES["F_fixed_scrap"][2],
                key="slider_f_scrap",
                help="Infrastructure cost: handling equipment, quality control, legal agreements"
            )
            st.session_state.cost_params["F_fixed_scrap"] = f_scrap
        
        st.info("💡 **Higher activation costs** → Optimizer creates fewer, larger-volume partnerships instead of many small connections")

    with cost_tab5: # type: ignore
        st.markdown("**Transportation Costs**")
        st.caption("Variable costs per unit of material per kilometer transported")
        col1, col2 = st.columns(2)
        with col1:
            t11 = st.slider(
                "🔥 Heat Transport (€/MWh·km)",
                min_value=COST_RANGES["T11"][0],
                max_value=COST_RANGES["T11"][1],
                value=st.session_state.cost_params.get("T11", DEFAULT_COST_PARAMS["T11"]),
                step=COST_RANGES["T11"][2],
                key="slider_t11",
                help="Cost to transport heat through insulated pipelines per MWh per km"
            )
            st.session_state.cost_params["T11"] = t11
        with col2:
            t23 = st.slider(
                "♻️ Scrap Transport (€/ton·km)",
                min_value=COST_RANGES["T23"][0],
                max_value=COST_RANGES["T23"][1],
                value=st.session_state.cost_params.get("T23", DEFAULT_COST_PARAMS["T23"]),
                step=COST_RANGES["T23"][2],
                key="slider_t23",
                help="Cost to transport scrap by truck per ton per km"
            )
            st.session_state.cost_params["T23"] = t23
        st.info("💡 **Higher transport costs** → Optimizer favors partnerships between geographically close firms")
    
    # Reset button
    col_reset1, col_reset2, col_reset3 = st.columns([1, 1, 1])
    with col_reset2:
        if st.button("🔄 Reset All Costs to Defaults", width='stretch'):
            st.session_state.cost_params = DEFAULT_COST_PARAMS.copy()
            st.success("✅ Cost parameters reset to default values")
            st.rerun()
    
    st.markdown("---")
    st.caption("💡 Recovery rates (γ) are configured in the 'Data Matrices' tab")
    
    # Show enabled synergies from Tab 2
    synergy_matrix = st.session_state.get("synergy_matrix")
    if synergy_matrix is not None:
        heat_enabled = synergy_matrix.loc["Waste heat", "Electricity"]
        scrap_enabled = synergy_matrix.loc["Plastic scrap", "Polymer"]
        steam_enabled = synergy_matrix.loc["Steam/Wastewater", "Water"]
        
        enabled_list = []
        if heat_enabled:
            enabled_list.append("🔥 Heat → Electricity")
        if steam_enabled:
            enabled_list.append("💧 Steam → Water")
        if scrap_enabled:
            enabled_list.append("♻️ Scrap → Polymer")
        
        if enabled_list:
            st.success(f"✅ **Active Synergies**: {', '.join(enabled_list)}")
        else:
            st.warning("⚠️ No synergies enabled! Please select at least one in 'Data Matrices' tab")
    
    st.markdown("---")
    
    # Professional Run Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_button = st.button(
            "🚀 Execute Optimization Pipeline",
            type="primary",
            width='stretch',
            help="Generate scenarios and solve optimization for each"
        )
    
    if run_button:
        # Progress tracking
        progress_container = st.container()
        
        with progress_container:
            st.markdown("""
            <div style='background: #f0f2f6; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #667eea;'>
                <h4 style='margin: 0 0 1rem 0;'>🔄 Optimization Pipeline Running...</h4>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Phase 1: Generate Scenarios
                status_text.markdown("**Phase 1/2:** Generating Monte Carlo scenarios...")
                progress_bar.progress(25)
                
                # Calculate distances
                coords_dict = {}
                for firm_id in ["F1", "F2", "F3", "F4", "F5"]:
                    firm_name = st.session_state.firm_locations[firm_id]["name"]
                    lat = st.session_state.firm_locations[firm_id]["lat"]
                    lon = st.session_state.firm_locations[firm_id]["lon"]
                    coords_dict[firm_name] = (lat, lon)

                names = list(coords_dict.keys())
                n = len(names)
                dist_matrix_combo = np.zeros((n, n))
                for i in range(n):
                    for j in range(n):
                        lat1, lon1 = coords_dict[names[i]]
                        lat2, lon2 = coords_dict[names[j]]
                        dist_matrix_combo[i, j] = haversine_km(lat1, lon1, lat2, lon2)

                progress_bar.progress(40)
                status_text.markdown(f"**Phase 1/2:** ✅ Generated {n_sim_combo} scenarios (S,D pairs)")
                
                # Phase 2: Optimize
                status_text.markdown(f"**Phase 2/2:** Optimizing {n_sim_combo} scenarios (finding optimal q & z)...")
                progress_bar.progress(50)

                # Get synergy matrix from Tab 2
                synergy_matrix = st.session_state.get("synergy_matrix")
                if synergy_matrix is None:
                    st.error("⚠️ Please configure synergies in 'Data Matrices' tab first")
                    st.stop()
                
                # Get recovery rates from Tab 2 (from session_state sliders)
                r11 = st.session_state.get("r11_matrix", 0.9)
                r23 = st.session_state.get("r23_matrix", 0.8)
                r_steam_water = st.session_state.get("r_steam_water_matrix", 0.85)
                
                # Get substitution share limits (delta) from Tab 2
                delta_heat_elec = st.session_state.get("delta_heat_elec_matrix", 1.0)
                delta_scrap_poly = st.session_state.get("delta_scrap_poly_matrix", 1.0)
                delta_steam_water = st.session_state.get("delta_steam_water_matrix", 1.0)
                
                # Run Monte Carlo + Optimization with enabled synergies and delta constraints
                df_runs_c, df_qz_c, sols_c, df_arcs_c, scenarios_sd_c = run_montecarlo(
                    S_il_base=st.session_state.S_il.values,
                    D_jk_base=st.session_state.D_jk.values,
                    dist_ij=dist_matrix_combo,
                    firm_names=["F1", "F2", "F3", "F4", "F5"],
                    cost_params=st.session_state.get("cost_params", DEFAULT_COST_PARAMS),
                    r11=r11,
                    r23=r23,
                    synergy_matrix=synergy_matrix,
                    delta_heat_elec=delta_heat_elec,
                    delta_scrap_poly=delta_scrap_poly,
                    delta_steam_water=delta_steam_water,
                    n_sim=n_sim_combo,
                    variation_pct=variation_pct_combo,
                    distribution_type=distribution_combo
                )

                progress_bar.progress(100)
                status_text.markdown("**Phase 2/2:** ✅ Optimization complete!")

                # Store results
                st.session_state.combo_results = {
                    "df_runs": df_runs_c,
                    "df_qz": df_qz_c,
                    "df_arcs": df_arcs_c,
                    "sols": sols_c,
                    "n_sim": n_sim_combo,
                    "scenarios_sd": scenarios_sd_c,
                }
                
                # Also store in mc_results for compatibility - use actual data sources
                df_flags = pd.DataFrame({
                    "Firm": ["F1", "F2", "F3", "F4", "F5"],
                    "DataSource": [
                        "REAL" if st.session_state.use_real_data.get(f, False) else "EIO" 
                        for f in ["F1", "F2", "F3", "F4", "F5"]
                    ]
                })
                df_flags_quality = add_data_quality_flags(df_flags)
                
                st.session_state.mc_results = {
                    "df_runs": df_runs_c,
                    "df_qz": df_qz_c,
                    "df_flags": df_flags_quality,
                    "df_arcs": df_arcs_c,
                    "sols": sols_c,
                }
                st.session_state.mc_run_complete = True

                # Success message
                st.balloons()
                st.success(f"""
                ✅ **Optimization Successfully Completed!**
                - Generated {n_sim_combo} unique (S,D) scenario pairs
                - Solved {n_sim_combo} MILP optimization problems
                - Found optimal q and z matrices for each scenario
                """)

                # Results Section
                st.markdown("---")
                st.markdown("""
                <div style='background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                            padding: 1.5rem; border-radius: 10px; margin: 2rem 0;'>
                    <h3 style='color: white; margin: 0;'>📊 Optimization Results Dashboard</h3>
                    <p style='color: white; margin: 0.5rem 0 0 0; opacity: 0.9;'>
                        Statistical analysis across all {n_sim_combo} optimized scenarios
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Key Performance Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    avg_cost = df_runs_c['objective_total'].mean()
                    std_cost = df_runs_c['objective_total'].std()
                    st.metric(
                        "💰 Average Total Cost",
                        f"€{avg_cost:,.0f}",
                        delta=f"σ = €{std_cost:,.0f}",
                        delta_color="inverse"
                    )
                with col2:
                    avg_heat = df_runs_c['total_heat_used'].mean()
                    std_heat = df_runs_c['total_heat_used'].std()
                    st.metric(
                        "🔥 Heat Utilized",
                        f"{avg_heat:.1f} MWh",
                        delta=f"σ = {std_heat:.1f}"
                    )
                with col3:
                    avg_scrap = df_runs_c['total_scrap_used'].mean()
                    std_scrap = df_runs_c['total_scrap_used'].std()
                    st.metric(
                        "♻️ Scrap Utilized",
                        f"{avg_scrap:.1f} tons",
                        delta=f"σ = {std_scrap:.1f}"
                    )
                with col4:
                    avg_arcs = df_runs_c['active_arcs'].mean()
                    std_arcs = df_runs_c['active_arcs'].std()
                    st.metric(
                        "🔗 Active Partnerships",
                        f"{avg_arcs:.1f}",
                        delta=f"σ = {std_arcs:.1f}"
                    )
                
                # Interactive Results Tabs
                st.markdown("---")
                result_tab1, result_tab2, result_tab3, result_tab4, result_tab5 = st.tabs([
                    "🔢 S & D Scenarios",
                    "✨ Optimal Solutions",
                    "📊 Statistical Analysis",
                    "🌐 Network Topology",
                    "📋 Complete Data"
                ])
                
                with result_tab1:
                    st.markdown("### 🔢 Generated Supply (S) and Demand (D) Scenarios")
                    st.markdown(f"""
                    This table shows all **{n_sim_combo}** randomized Supply-Demand pairs generated by the Monte Carlo 
                    simulation. Each row represents one possible future state of the industrial network under uncertainty.
                    """)
                    
                    with st.expander("📖 Understanding S & D Scenarios"):
                        st.markdown(f"""
                        **What are these scenarios?**
                        
                        Each scenario is a **randomized variation** of the base Supply and Demand values you configured 
                        in the "Firms Management" tab. The Monte Carlo method explores how the optimal symbiosis network 
                        changes when S and D values fluctuate (due to production variations, seasonal effects, etc.).
                        
                        **How are they generated?**
                        
                        For each firm and each resource:
                        
                        $$
                        S_{{\\text{{scenario}}}} = S_{{\\text{{base}}}} \\times (1 + \\text{{random variation}})
                        $$
                        
                        - **Base values**: What you configured in Tab 1
                        - **Random variation**: ±{variation_pct_combo}% using **{distribution_combo}** distribution
                        - Each value varies **independently**
                        
                        **Column Nomenclature:**
                        
                        | Column Format | Meaning | Example |
                        |--------------|---------|---------|
                        | `S_F#_Heat` | Supply of Heat from Firm # | S_F1_Heat = 103.7 MWh available |
                        | `S_F#_Scrap` | Supply of Scrap from Firm # | S_F2_Scrap = 268.5 tons available |
                        | `D_F#_Elec` | Demand for Electricity by Firm # | D_F3_Elec = 89.96 MWh needed |
                        | `D_F#_Poly` | Demand for Polymer by Firm # | D_F4_Poly = 245.3 tons needed |
                        
                        **Example Interpretation:**
                        
                        **Scenario S001**: Cost = €42,150
                        - Firm 1 has **103.7 MWh** of waste heat available (not a sum, individual value)
                        - Firm 1 needs **89.96 MWh** of electricity
                        - Given these S,D values → optimizer found partnerships costing €42,150
                        
                        **Why is this useful?**
                        - See how S,D variations affect optimal costs
                        - Identify worst-case scenarios (highest costs)
                        - Understand which resources have most impact on cost (via sensitivity)
                        - Plan for uncertainty: "What if production increases/decreases?"
                        """)
                    
                    st.markdown("---")
                    
                    # Visual summary of variation
                    st.markdown("#### 📊 Scenario Variation Summary")
                    summary_cols = st.columns(4)
                    
                    # Calculate total S and D across all scenarios
                    total_heat_supply = sum([s["S_il"][:, 0].sum() for s in scenarios_sd_c])
                    total_scrap_supply = sum([s["S_il"][:, 1].sum() for s in scenarios_sd_c])
                    total_elec_demand = sum([s["D_jk"][:, 0].sum() for s in scenarios_sd_c])
                    total_poly_demand = sum([s["D_jk"][:, 1].sum() for s in scenarios_sd_c])
                    
                    with summary_cols[0]:
                        st.metric(
                            "🔥 Avg Heat Supply",
                            f"{total_heat_supply/n_sim_combo:.1f} MWh",
                            delta=f"Range: ±{variation_pct_combo}%"
                        )
                    with summary_cols[1]:
                        st.metric(
                            "♻️ Avg Scrap Supply",
                            f"{total_scrap_supply/n_sim_combo:.1f} tons",
                            delta=f"Range: ±{variation_pct_combo}%"
                        )
                    with summary_cols[2]:
                        st.metric(
                            "⚡ Avg Electricity Demand",
                            f"{total_elec_demand/n_sim_combo:.1f} MWh",
                            delta=f"Range: ±{variation_pct_combo}%"
                        )
                    with summary_cols[3]:
                        st.metric(
                            "🧪 Avg Polymer Demand",
                            f"{total_poly_demand/n_sim_combo:.1f} tons",
                            delta=f"Range: ±{variation_pct_combo}%"
                        )
                    
                    st.markdown("---")
                    
                    # Create a comprehensive table with all S and D values
                    sd_table_data = []
                    for scenario in scenarios_sd_c:
                        sid = scenario["scenario_id"]
                        S_il = scenario["S_il"]
                        D_jk = scenario["D_jk"]
                        
                        # Get objective for this scenario
                        obj_val = df_runs_c[df_runs_c["scenario_id"] == sid]["objective_total"].values[0]
                        
                        # Handle None values (failed optimizations)
                        cost_str = f"{obj_val:,.0f}" if obj_val is not None else "N/A"
                        row = {"Scenario": sid, "Cost (€)": cost_str}
                        
                        # Add Supply values (Heat, Scrap) for each firm
                        for i in range(5):
                            row[f"S_F{i+1}_Heat"] = S_il[i, 0]
                            row[f"S_F{i+1}_Scrap"] = S_il[i, 1]
                        
                        # Add Demand values (Electricity, Polymer) for each firm
                        for i in range(5):
                            row[f"D_F{i+1}_Elec"] = D_jk[i, 0]
                            row[f"D_F{i+1}_Poly"] = D_jk[i, 1]
                        
                        sd_table_data.append(row)
                    
                    df_sd_table = pd.DataFrame(sd_table_data)
                    
                    # Display with filters
                    st.markdown("#### 📋 Full S & D Scenarios Table")
                    
                    # Info box
                    st.info(f"""
                    💡 **Table contains:** {n_sim_combo} scenarios × (10 Supply values + 10 Demand values) = {n_sim_combo * 20} data points
                    - **Distribution type:** {distribution_combo.title()}
                    - **Variation:** ±{variation_pct_combo}% from baseline
                    """)
                    
                    # Add download button
                    csv = df_sd_table.to_csv(index=False)
                    st.download_button(
                        label="📥 Download S & D Scenarios as CSV",
                        data=csv,
                        file_name=f"sd_scenarios_{n_sim_combo}.csv",
                        mime="text/csv"
                    )
                    
                    # Display table with formatting
                    st.dataframe(
                        df_sd_table.style.format({
                            col: "{:.2f}" for col in df_sd_table.columns if col not in ["Scenario", "Cost (€)"]
                        }),
                        width='stretch',
                        height=500
                    )
                    
                    # Statistics summary
                    st.markdown("---")
                    st.markdown("#### 📊 Supply & Demand Statistics Across All Scenarios")
                    
                    col_stats1, col_stats2 = st.columns(2)
                    
                    with col_stats1:
                        st.markdown("**Supply (S) Statistics**")
                        s_cols = [col for col in df_sd_table.columns if col.startswith("S_")]
                        stats_s = df_sd_table[s_cols].describe().T
                        stats_s.index = [col.replace("S_", "") for col in s_cols]
                        st.dataframe(stats_s.style.format("{:.2f}"), width='stretch')
                    
                    with col_stats2:
                        st.markdown("**Demand (D) Statistics**")
                        d_cols = [col for col in df_sd_table.columns if col.startswith("D_")]
                        stats_d = df_sd_table[d_cols].describe().T
                        stats_d.index = [col.replace("D_", "") for col in d_cols]
                        st.dataframe(stats_d.style.format("{:.2f}"), width='stretch')
                
                with result_tab2:
                    st.markdown("### ✨ Optimal Solutions Analysis (q* & z*)")
                    st.markdown("""
                    This section shows the **optimal partnership configurations** found by the MILP optimizer. 
                    The results are presented in two ways: **aggregate statistics** across all scenarios (to identify 
                    robust patterns) and **individual scenario details** (for verification).
                    """)
                    
                    with st.expander("🧮 Understanding the Optimization Problem"):
                        st.markdown("""
                        **What the Optimizer Does:**
                        
                        For each (S,D) scenario, the MILP solver finds the optimal values of:
                        - **q***: Flow quantities (MWh, tons) between each pair of firms
                        - **z***: Binary decisions (0/1) indicating which partnerships to activate
                        
                        **Mathematical Formulation:**
                        
                        $$
                        \\min_{q,z} \\quad C_{\\text{total}}(q, z) = C_{\\text{virgin}} + C_{\\text{disposal}} + C_{\\text{recovery}} + C_{\\text{activation}} + C_{\\text{transport}}
                        $$
                        
                        **Subject to:**
                        - Supply constraints: Cannot exceed available waste
                        - Demand constraints: Must meet input requirements
                        - Big-M constraints: q[i,j] = 0 if z[i,j] = 0 (no flow without activated partnership)
                        - δ constraints: Recovered inputs ≤ δ × Demand (substitution limits)
                        
                        **Why This Matters:**
                        - The optimizer balances multiple costs to find the **economically optimal** network
                        - Different (S,D) scenarios lead to different optimal configurations
                        - Aggregate analysis reveals which partnerships are **consistently optimal** (robust)
                        """)
                    
                    st.markdown("---")
                    
                    # AGGREGATE ANALYSIS FIRST
                    st.markdown("### 📊 Aggregate Analysis Across All Scenarios")
                    st.caption(f"Statistical summary of optimal solutions from {n_sim_combo} optimizations")
                    
                    # Calculate aggregate statistics for partnerships
                    partnership_freq_heat = np.zeros((5, 5))
                    partnership_freq_scrap = np.zeros((5, 5))
                    flow_sum_heat = np.zeros((5, 5))
                    flow_sum_scrap = np.zeros((5, 5))
                    flow_max_heat = np.zeros((5, 5))
                    flow_max_scrap = np.zeros((5, 5))
                    
                    for sol in sols_c:
                        partnership_freq_heat += np.array(sol["z11"])
                        partnership_freq_scrap += np.array(sol["z23"])
                        q11_arr = np.array(sol["q11"])
                        q23_arr = np.array(sol["q23"])
                        flow_sum_heat += q11_arr
                        flow_sum_scrap += q23_arr
                        flow_max_heat = np.maximum(flow_max_heat, q11_arr)
                        flow_max_scrap = np.maximum(flow_max_scrap, q23_arr)
                    
                    # Convert to percentages and averages
                    partnership_pct_heat = (partnership_freq_heat / n_sim_combo) * 100
                    partnership_pct_scrap = (partnership_freq_scrap / n_sim_combo) * 100
                    flow_avg_heat = flow_sum_heat / n_sim_combo
                    flow_avg_scrap = flow_sum_scrap / n_sim_combo
                    
                    # Display aggregate results
                    st.markdown("#### 🔥 Heat → Electricity Aggregated Results")
                    
                    col_agg1, col_agg2, col_agg3 = st.columns(3)
                    
                    with col_agg1:
                        st.markdown("**Partnership Frequency [%]**")
                        st.caption(f"How often each connection was activated (out of {n_sim_combo} scenarios)")
                        freq_heat_df = pd.DataFrame(partnership_pct_heat, index=names, columns=names)
                        st.dataframe(
                            freq_heat_df.style.format("{:.1f}%").background_gradient(cmap="Reds", axis=None, vmin=0, vmax=100),
                            width='stretch'
                        )
                        
                    with col_agg2:
                        st.markdown("**Average Flow [MWh]**")
                        st.caption("Average heat flow when connection is active")
                        avg_heat_df = pd.DataFrame(flow_avg_heat, index=names, columns=names)
                        st.dataframe(
                            avg_heat_df.style.format("{:.2f}").background_gradient(cmap="YlOrRd", axis=None),
                            width='stretch'
                        )
                    
                    with col_agg3:
                        st.markdown("**Maximum Flow [MWh]**")
                        st.caption("Peak heat flow observed across all scenarios")
                        max_heat_df = pd.DataFrame(flow_max_heat, index=names, columns=names)
                        st.dataframe(
                            max_heat_df.style.format("{:.2f}").background_gradient(cmap="Oranges", axis=None),
                            width='stretch'
                        )
                    
                    st.markdown("---")
                    st.markdown("#### ♻️ Scrap → Polymer Aggregated Results")
                    
                    col_agg4, col_agg5, col_agg6 = st.columns(3)
                    
                    with col_agg4:
                        st.markdown("**Partnership Frequency [%]**")
                        st.caption(f"How often each connection was activated (out of {n_sim_combo} scenarios)")
                        freq_scrap_df = pd.DataFrame(partnership_pct_scrap, index=names, columns=names)
                        st.dataframe(
                            freq_scrap_df.style.format("{:.1f}%").background_gradient(cmap="Blues", axis=None, vmin=0, vmax=100),
                            width='stretch'
                        )
                        
                    with col_agg5:
                        st.markdown("**Average Flow [tons]**")
                        st.caption("Average scrap flow when connection is active")
                        avg_scrap_df = pd.DataFrame(flow_avg_scrap, index=names, columns=names)
                        st.dataframe(
                            avg_scrap_df.style.format("{:.2f}").background_gradient(cmap="YlGnBu", axis=None),
                            width='stretch'
                        )
                    
                    with col_agg6:
                        st.markdown("**Maximum Flow [tons]**")
                        st.caption("Peak scrap flow observed across all scenarios")
                        max_scrap_df = pd.DataFrame(flow_max_scrap, index=names, columns=names)
                        st.dataframe(
                            max_scrap_df.style.format("{:.2f}").background_gradient(cmap="Greens", axis=None),
                            width='stretch'
                        )
                    
                    # Partnership robustness insights
                    st.markdown("---")
                    st.markdown("#### 🎯 Partnership Robustness Analysis")
                    
                    col_rob1, col_rob2 = st.columns(2)
                    
                    with col_rob1:
                        st.markdown("**🔥 Most Robust Heat Partnerships**")
                        # Find partnerships active in >70% of scenarios
                        robust_heat = []
                        for i in range(5):
                            for j in range(5):
                                if partnership_pct_heat[i, j] > 70:
                                    robust_heat.append({
                                        "From": names[i],
                                        "To": names[j],
                                        "Frequency": f"{partnership_pct_heat[i, j]:.1f}%",
                                        "Avg Flow": f"{flow_avg_heat[i, j]:.2f} MWh"
                                    })
                        
                        if robust_heat:
                            df_robust_heat = pd.DataFrame(robust_heat)
                            st.dataframe(df_robust_heat, width='stretch', hide_index=True)
                        else:
                            st.info("No partnerships active in >70% of scenarios")
                    
                    with col_rob2:
                        st.markdown("**♻️ Most Robust Scrap Partnerships**")
                        # Find partnerships active in >70% of scenarios
                        robust_scrap = []
                        for i in range(5):
                            for j in range(5):
                                if partnership_pct_scrap[i, j] > 70:
                                    robust_scrap.append({
                                        "From": names[i],
                                        "To": names[j],
                                        "Frequency": f"{partnership_pct_scrap[i, j]:.1f}%",
                                        "Avg Flow": f"{flow_avg_scrap[i, j]:.2f} tons"
                                    })
                        
                        if robust_scrap:
                            df_robust_scrap = pd.DataFrame(robust_scrap)
                            st.dataframe(df_robust_scrap, width='stretch', hide_index=True)
                        else:
                            st.info("No partnerships active in >70% of scenarios")
                    
                    st.markdown("---")
                    
                    # INDIVIDUAL SCENARIO EXPLORER (optional, collapsed)
                    with st.expander("🔎 Explore Individual Scenarios (Optional)", expanded=False):
                        st.caption("Select a specific scenario to view its exact q* and z* matrices")
                        
                        col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
                        with col_sel1:
                            sid_options = df_runs_c["scenario_id"].tolist()
                            sid_sel = st.selectbox(
                                "Select Scenario",
                                sid_options,
                                key="combo_sid",
                                help="Choose a scenario to view its optimal q and z matrices"
                            )
                        with col_sel2:
                            # Show scenario rank
                            scenario_row = df_runs_c[df_runs_c["scenario_id"] == sid_sel].iloc[0]
                            cost_col = 'objective_total' if 'objective_total' in df_runs_c.columns else 'total_cost'
                            rank = (df_runs_c[cost_col] <= scenario_row[cost_col]).sum()
                            st.metric("Cost Rank", f"{rank}/{len(df_runs_c)}")
                        with col_sel3:
                            cost_col = 'objective_total' if 'objective_total' in scenario_row.index else 'total_cost'
                            st.metric("Total Cost", f"€{scenario_row[cost_col]:,.0f}")
                        
                        # Find selected solution
                        sol_sel = None
                        for s in sols_c:
                            if s.get("scenario_id") == sid_sel:
                                sol_sel = s
                                break
                        
                        if sol_sel is not None:
                            st.markdown("---")
                            st.markdown("**📐 Exact Optimal Values for This Scenario**")
                            
                            # Heat-Electricity Exchange
                            st.markdown("**🔥 Heat → Electricity (q*₁₁, z*₁₁)**")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("*Flow Quantities [MWh]*")
                                q11_df = pd.DataFrame(sol_sel["q11"], index=names, columns=names)
                                st.dataframe(
                                    q11_df.style.format("{:.2f}").background_gradient(cmap="YlOrRd", axis=None),
                                    width='stretch'
                                )
                            
                            with col2:
                                st.markdown("*Binary Connections [0/1]*")
                                z11_df = pd.DataFrame(sol_sel["z11"], index=names, columns=names)
                                st.dataframe(
                                    z11_df.style.format("{:.0f}").background_gradient(cmap="Greys", axis=None, vmin=0, vmax=1),
                                    width='stretch'
                                )
                            
                            # Scrap-Polymer Exchange
                            st.markdown("**♻️ Scrap → Polymer (q*₂₃, z*₂₃)**")
                            
                            col3, col4 = st.columns(2)
                            
                            with col3:
                                st.markdown("*Flow Quantities [tons]*")
                                q23_df = pd.DataFrame(sol_sel["q23"], index=names, columns=names)
                                st.dataframe(
                                    q23_df.style.format("{:.2f}").background_gradient(cmap="YlGnBu", axis=None),
                                    width='stretch'
                                )
                            
                            with col4:
                                st.markdown("*Binary Connections [0/1]*")
                                z23_df = pd.DataFrame(sol_sel["z23"], index=names, columns=names)
                                st.dataframe(
                                    z23_df.style.format("{:.0f}").background_gradient(cmap="Greys", axis=None, vmin=0, vmax=1),
                                    width='stretch'
                                )
                            # Cost breakdown for this scenario
                            if "cost_breakdown" in sol_sel:
                                st.markdown("---")
                                st.markdown("**💶 Cost Breakdown for This Scenario**")
                                cb = sol_sel["cost_breakdown"]
                                
                                # 5 columnas para todos los componentes de costo
                                col_cb1, col_cb2, col_cb3, col_cb4, col_cb5 = st.columns(5)
                                
                                with col_cb1:
                                    st.markdown("**🗑️ Disposal**")
                                    st.metric("Heat", f"€{cb.get('disposal_heat', 0):,.0f}")
                                    st.metric("Scrap", f"€{cb.get('disposal_scrap', 0):,.0f}")
                                
                                with col_cb2:
                                    st.markdown("**🏭 Virgin Inputs**")
                                    st.metric("Electricity", f"€{cb.get('virgin_elec', 0):,.0f}")
                                    st.metric("Polymer", f"€{cb.get('virgin_poly', 0):,.0f}")
                                
                                with col_cb3:
                                    st.markdown("**♻️ Recovery**")
                                    st.metric("Heat Use", f"€{cb.get('recovery_heat', 0):,.0f}")
                                    st.metric("Scrap Use", f"€{cb.get('recovery_scrap', 0):,.0f}")
                                
                                with col_cb4:
                                    st.markdown("**🔗 Activation**")
                                    st.metric("Heat Links", f"€{cb.get('activation_heat', 0):,.0f}")
                                    st.metric("Scrap Links", f"€{cb.get('activation_scrap', 0):,.0f}")
                                
                                with col_cb5:
                                    st.markdown("**🚚 Transport**")
                                    st.metric("Heat", f"€{cb.get('transport_heat', 0):,.0f}")
                                    st.metric("Scrap", f"€{cb.get('transport_scrap', 0):,.0f}")
                        else:
                            st.warning("⚠️ No solution found for selected scenario")
                    
                    # Interpretation guide
                    st.markdown("---")
                    with st.expander("📖 How to Interpret These Results"):
                        st.markdown("""
                        **Aggregate Analysis (Top Section):**
                        - **Partnership Frequency**: % of scenarios where optimizer activated this link
                          - 100% = Always optimal (very robust partnership)
                          - 50% = Sometimes optimal (depends on S,D variation)
                          - 0% = Never optimal (not economically viable)
                        - **Average Flow**: Mean quantity when partnership is active
                        - **Maximum Flow**: Highest flow observed across all scenarios
                        
                        **Reading the Matrices:**
                        - **Rows** = Supplier firms (providing waste)
                        - **Columns** = Consumer firms (receiving resource)
                        - **Value [i,j]** = Connection from firm i to firm j
                        
                        **Example Interpretations:**
                        - Partnership Frequency[F1,F3] = 95% → "Firm 1 sending heat to Firm 3 is optimal in 95% of scenarios"
                        - Average Flow[F1,F3] = 25.3 MWh → "When active, Firm 1 sends avg 25.3 MWh to Firm 3"
                        - Partnership Frequency[F2,F5] = 0% → "Firm 2 to Firm 5 connection never economically optimal"
                        
                        **Why is this useful?**
                        - Identifies **robust partnerships** that work under uncertainty
                        - Shows which connections are **sensitive** to S,D variations
                        - Helps prioritize infrastructure investments (focus on high-frequency links)
                        """)
                
                with result_tab3:
                    st.markdown("### 📈 Statistical Distribution Analysis")
                    st.markdown("""
                    Visualize how optimization results vary across all scenarios. These distributions reveal 
                    the **sensitivity** of the symbiosis network to uncertainty in supply and demand.
                    """)
                    
                    with st.expander("📊 How to Interpret These Charts"):
                        st.markdown("""
                        **Total Cost Distribution (Left Chart):**
                        - **Histogram**: Shows frequency of cost values across scenarios
                        - **Red dashed line**: Mean (average) total cost
                        - **Wide spread** → High sensitivity to S,D variations (risky)
                        - **Narrow peak** → Robust network (stable costs)
                        
                        **Resource Utilization Scatter Plot (Right Chart):**
                        - **X-axis**: Heat utilized (MWh)
                        - **Y-axis**: Scrap utilized (tons)
                        - **Color**: Total cost (darker = more expensive)
                        - **Pattern analysis**:
                          - Top-right corner = High resource use (sustainable)
                          - Bottom-left corner = Low resource use (inefficient)
                          - Color gradient reveals cost-efficiency relationship
                        
                        **Summary Statistics Table (Bottom):**
                        - **count**: Number of scenarios analyzed
                        - **mean**: Average value (central tendency)
                        - **std**: Standard deviation (variability/risk)
                        - **min/max**: Best and worst case scenarios
                        - **25%, 50%, 75%**: Percentiles (quartiles for distribution shape)
                        
                        **Key Insights to Look For:**
                        - High std in `objective_total` → Cost uncertainty is high
                        - Low std in `total_heat_used` → Consistent resource recovery
                        - Correlation between heat/scrap use and cost → Economies of scale?
                        """)
                    
                    st.markdown("---")
                    
                    # Cost distribution
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        st.markdown("**Total Cost Distribution**")
                        import matplotlib.pyplot as plt
                        fig1, ax1 = plt.subplots(figsize=(6, 4))
                        ax1.hist(df_runs_c['objective_total'], bins=20, color='#667eea', alpha=0.7, edgecolor='black')
                        ax1.axvline(avg_cost, color='red', linestyle='--', linewidth=2, label=f'Mean: €{avg_cost:,.0f}')
                        ax1.set_xlabel('Total Cost (€)')
                        ax1.set_ylabel('Frequency')
                        ax1.legend()
                        ax1.grid(alpha=0.3)
                        st.pyplot(fig1)
                    
                    with col_chart2:
                        st.markdown("**Resource Utilization**")
                        fig2, ax2 = plt.subplots(figsize=(6, 4))
                        ax2.scatter(df_runs_c['total_heat_used'], df_runs_c['total_scrap_used'], 
                                   c=df_runs_c['objective_total'], cmap='viridis', alpha=0.6, s=50)
                        ax2.set_xlabel('Heat Used (MWh)')
                        ax2.set_ylabel('Scrap Used (tons)')
                        cbar = plt.colorbar(ax2.collections[0], ax=ax2)
                        cbar.set_label('Total Cost (€)')
                        ax2.grid(alpha=0.3)
                        st.pyplot(fig2)
                    
                    # Summary statistics table
                    st.markdown("---")
                    st.markdown("#### 📊 Summary Statistics")
                    st.caption("Comprehensive statistical measures across all optimization scenarios")
                    
                    stats_df = df_runs_c[['objective_total', 'total_heat_used', 'total_scrap_used', 'active_arcs']].describe()
                    st.dataframe(stats_df.style.format("{:.2f}"), width='stretch')
                    
                    # Interpretation insights
                    st.markdown("---")
                    st.markdown("#### 💡 Statistical Insights")
                    
                    col_insight1, col_insight2 = st.columns(2)
                    
                    with col_insight1:
                        st.markdown("**📈 Variability Analysis**")
                        cv_cost = (df_runs_c['objective_total'].std() / df_runs_c['objective_total'].mean()) * 100
                        cv_heat = (df_runs_c['total_heat_used'].std() / df_runs_c['total_heat_used'].mean()) * 100
                        
                        if cv_cost > 20:
                            st.warning(f"⚠️ **High cost uncertainty**: CV = {cv_cost:.1f}% - Consider risk mitigation strategies")
                        else:
                            st.success(f"✅ **Stable costs**: CV = {cv_cost:.1f}% - Network is robust to S,D variations")
                        
                        st.info(f"📊 Heat utilization variability: CV = {cv_heat:.1f}%")
                    
                    with col_insight2:
                        st.markdown("**🎯 Distribution Shape**")
                        median_cost = df_runs_c['objective_total'].median()
                        mean_cost = df_runs_c['objective_total'].mean()
                        skewness = (mean_cost - median_cost) / df_runs_c['objective_total'].std()
                        
                        if abs(skewness) < 0.1:
                            st.info("📊 **Symmetric distribution** - Mean ≈ Median (normal-like)")
                        elif skewness > 0:
                            st.warning("📊 **Right-skewed** - More high-cost outliers than low-cost")
                        else:
                            st.success("📊 **Left-skewed** - More low-cost scenarios (favorable)")
                        
                        iqr = df_runs_c['objective_total'].quantile(0.75) - df_runs_c['objective_total'].quantile(0.25)
                        st.metric("Interquartile Range (IQR)", f"€{iqr:,.0f}", "Middle 50% of scenarios")
                
                with result_tab4:
                    st.markdown("### 🌐 Network Topology Analysis")
                    st.markdown("""
                    Interactive network visualization showing the industrial symbiosis partnerships. 
                    Node size represents firm activity, edge thickness represents partnership strength.
                    """)
                    
                    with st.expander("📖 How to Read the Network Diagram"):
                        st.markdown("""
                        **Network Elements:**
                        - **Nodes (circles)**: Firms in the industrial symbiosis network
                        - **Edges (arrows)**: Material/energy flows between firms
                        - **Edge thickness**: Proportional to partnership frequency (% of scenarios)
                        - **Edge color**: Red = Heat exchange, Blue = Scrap exchange
                        
                        **Interpretation:**
                        - **Thick edges**: Robust partnerships (active in many scenarios)
                        - **Thin edges**: Occasional partnerships (scenario-dependent)
                        - **No edge**: Connection never economically optimal
                        - **Isolated nodes**: Firms with few symbiotic relationships
                        """)
                    
                    st.markdown("---")
                    
                    # Network visualization options
                    col_viz1, col_viz2 = st.columns(2)
                    
                    with col_viz1:
                        viz_resource = st.selectbox(
                            "Select Resource Flow",
                            ["Heat → Electricity", "Scrap → Polymer", "Combined"],
                            key="viz_resource"
                        )
                    
                    with col_viz2:
                        min_frequency = st.slider(
                            "Minimum Partnership Frequency (%)",
                            min_value=0, max_value=100, value=10, step=5,
                            key="min_freq",
                            help="Only show partnerships active in at least this % of scenarios"
                        )
                    
                    st.markdown("---")
                    
                    # Create network graph
                    try:
                        import networkx as nx
                        import matplotlib.pyplot as plt
                        
                        # Create directed graph
                        G = nx.DiGraph()
                        
                        # Add all firms as nodes
                        for firm in names:
                            G.add_node(firm)
                        
                        # Add edges based on selected resource
                        edge_list = []
                        
                        if viz_resource in ["Heat → Electricity", "Combined"]:
                            for i in range(5):
                                for j in range(5):
                                    freq = partnership_pct_heat[i, j]
                                    if freq >= min_frequency and i != j:
                                        weight = freq / 100.0
                                        avg_flow = flow_avg_heat[i, j]
                                        G.add_edge(names[i], names[j], 
                                                 weight=weight, 
                                                 flow=avg_flow,
                                                 color='red',
                                                 label=f"{freq:.0f}%\n{avg_flow:.1f} MWh")
                                        edge_list.append((names[i], names[j], weight, 'red'))
                        
                        if viz_resource in ["Scrap → Polymer", "Combined"]:
                            for i in range(5):
                                for j in range(5):
                                    freq = partnership_pct_scrap[i, j]
                                    if freq >= min_frequency and i != j:
                                        weight = freq / 100.0
                                        avg_flow = flow_avg_scrap[i, j]
                                        if G.has_edge(names[i], names[j]):
                                            # Combined edge
                                            G.edges[names[i], names[j]]['color'] = 'purple'
                                            G.edges[names[i], names[j]]['label'] += f"\n{freq:.0f}%\n{avg_flow:.1f} t"
                                        else:
                                            G.add_edge(names[i], names[j], 
                                                     weight=weight, 
                                                     flow=avg_flow,
                                                     color='blue',
                                                     label=f"{freq:.0f}%\n{avg_flow:.1f} t")
                                            edge_list.append((names[i], names[j], weight, 'blue'))
                        
                        # Check if there are edges to display
                        if G.number_of_edges() == 0:
                            st.warning(f"⚠️ No partnerships found with frequency ≥ {min_frequency}%. Try lowering the minimum frequency threshold.")
                        else:
                            # Create visualization
                            fig, ax = plt.subplots(figsize=(12, 8))
                            
                            # Use spring layout for better visualization
                            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
                            
                            # Draw nodes
                            nx.draw_networkx_nodes(G, pos, 
                                                 node_color='lightgreen',
                                                 node_size=3000,
                                                 alpha=0.9,
                                                 ax=ax)
                            
                            # Draw edges with varying thickness based on weight
                            edges = G.edges()
                            weights = [G[u][v]['weight'] * 5 for u, v in edges]
                            colors = [G[u][v]['color'] for u, v in edges]
                            
                            nx.draw_networkx_edges(G, pos,
                                                 edgelist=edges,
                                                 width=weights,
                                                 edge_color=colors,
                                                 alpha=0.6,
                                                 arrows=True,
                                                 arrowsize=20,
                                                 arrowstyle='->',
                                                 connectionstyle='arc3,rad=0.1',
                                                 ax=ax)
                            
                            # Draw labels
                            nx.draw_networkx_labels(G, pos,
                                                  font_size=12,
                                                  font_weight='bold',
                                                  ax=ax)
                            
                            ax.set_title(f"Industrial Symbiosis Network - {viz_resource}\n(Min. Frequency: {min_frequency}%)", 
                                       fontsize=14, fontweight='bold')
                            ax.axis('off')
                            
                            # Add legend
                            from matplotlib.patches import Patch
                            legend_elements = []
                            if viz_resource in ["Heat → Electricity", "Combined"]:
                                legend_elements.append(Patch(facecolor='red', alpha=0.6, label='Heat → Electricity'))
                            if viz_resource in ["Scrap → Polymer", "Combined"]:
                                legend_elements.append(Patch(facecolor='blue', alpha=0.6, label='Scrap → Polymer'))
                            if viz_resource == "Combined":
                                legend_elements.append(Patch(facecolor='purple', alpha=0.6, label='Both Resources'))
                            
                            ax.legend(handles=legend_elements, loc='upper right')
                            
                            st.pyplot(fig)
                            
                            # Network statistics
                            st.markdown("---")
                            st.markdown("#### 📊 Network Statistics")
                            
                            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                            
                            with col_stat1:
                                st.metric("Total Firms", G.number_of_nodes())
                            
                            with col_stat2:
                                st.metric("Active Partnerships", G.number_of_edges())
                            
                            with col_stat3:
                                avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes()
                                st.metric("Avg Connections/Firm", f"{avg_degree:.1f}")
                            
                            with col_stat4:
                                density = nx.density(G)
                                st.metric("Network Density", f"{density:.2%}")
                            
                            # Most connected firms
                            st.markdown("---")
                            st.markdown("#### 🏆 Most Connected Firms")
                            
                            col_conn1, col_conn2 = st.columns(2)
                            
                            with col_conn1:
                                st.markdown("**As Suppliers (Outgoing)**")
                                out_degree = dict(G.out_degree())
                                sorted_out = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)
                                for firm, degree in sorted_out[:3]:
                                    st.write(f"• **{firm}**: {degree} partnerships")
                            
                            with col_conn2:
                                st.markdown("**As Consumers (Incoming)**")
                                in_degree = dict(G.in_degree())
                                sorted_in = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)
                                for firm, degree in sorted_in[:3]:
                                    st.write(f"• **{firm}**: {degree} partnerships")
                    
                    except ImportError:
                        st.error("📦 NetworkX library not installed. Install with: `pip install networkx`")
                    except Exception as e:
                        st.error(f"❌ Error creating network visualization: {str(e)}")
                        st.code(traceback.format_exc())
                
                with result_tab5:
                    st.markdown("### 📋 Complete Scenarios Table")
                    st.markdown("""
                    This table contains **all optimization results** for each scenario. Each row represents one 
                    optimized scenario with its associated costs and resource utilization metrics.
                    """)
                    
                    # Explanation of columns
                    with st.expander("📖 Understanding the Table Columns"):
                        st.markdown("""
                        **Key Metrics for Each Scenario:**
                        
                        | Column | Description | Interpretation |
                        |--------|-------------|----------------|
                        | **scenario_id** | Unique identifier (S001, S002, ...) | Links to S,D pairs in "S & D Scenarios" tab |
                        | **status** | Solver status | "Optimal" = solution found ✅ |
                        | **objective_total** | Total cost (€) | MILP objective function value - **lower is better** |
                        | **total_heat_used** | Heat exchanged (MWh) | Σᵢⱼ q₁₁[i,j] - total waste heat utilized |
                        | **total_scrap_used** | Scrap exchanged (tons) | Σᵢⱼ q₂₃[i,j] - total plastic scrap recycled |
                        | **active_arcs** | Active partnerships | Σᵢⱼ (z₁₁[i,j] + z₂₃[i,j]) - number of firm connections |
                        
                        **How to Use This Table:**
                        - **Sort by `objective_total`** → Find most economical scenarios
                        - **Sort by `total_heat_used`** → Find scenarios with maximum waste recovery
                        - **Filter by `active_arcs`** → Analyze network complexity vs. cost
                        - **Click on `scenario_id`** → Cross-reference with other tabs for details
                        
                        **Example Analysis:**
                        - Low cost + high resource use + few arcs = **Efficient concentrated network**
                        - High cost + low resource use + many arcs = **Inefficient dispersed network**
                        - Look for patterns: Do geographically close firms always have lower costs?
                        """)
                    
                    # Display the table
                    st.dataframe(
                        df_runs_c.style.format({
                            'objective_total': '€{:,.0f}',
                            'total_heat_used': '{:.2f}',
                            'total_scrap_used': '{:.2f}',
                            'active_arcs': '{:.0f}'
                        }),
                        width='stretch',
                        height=400
                    )
                    
                    # Quick stats summary
                    st.markdown("---")
                    st.markdown("#### 📊 Quick Summary")
                    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
                    
                    with col_sum1:
                        best_scenario = df_runs_c.loc[df_runs_c['objective_total'].idxmin()]
                        st.metric(
                            "💰 Best Scenario",
                            best_scenario['scenario_id'],
                            f"€{best_scenario['objective_total']:,.0f}"
                        )
                    
                    with col_sum2:
                        worst_scenario = df_runs_c.loc[df_runs_c['objective_total'].idxmax()]
                        st.metric(
                            "📈 Worst Scenario",
                            worst_scenario['scenario_id'],
                            f"€{worst_scenario['objective_total']:,.0f}"
                        )
                    
                    with col_sum3:
                        max_heat_scenario = df_runs_c.loc[df_runs_c['total_heat_used'].idxmax()]
                        st.metric(
                            "🔥 Max Heat Use",
                            max_heat_scenario['scenario_id'],
                            f"{max_heat_scenario['total_heat_used']:.1f} MWh"
                        )
                    
                    with col_sum4:
                        cost_range = df_runs_c['objective_total'].max() - df_runs_c['objective_total'].min()
                        st.metric(
                            "📊 Cost Variability",
                            f"€{cost_range:,.0f}",
                            f"{(cost_range/df_runs_c['objective_total'].mean())*100:.1f}%"
                        )

            except Exception as e:
                st.error(f"❌ Error during optimization: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# ============================================
# TAB 4: NETWORK VISUALIZATION
# ============================================
with tab4:

    
    # Check if Monte Carlo has been run
    df_qz = st.session_state.get("mc_results", {}).get("df_qz") if st.session_state.get("mc_run_complete", False) else None
    
    if df_qz is None or (isinstance(df_qz, pd.DataFrame) and df_qz.empty):
        st.info("⚠️ Run the optimization first (Tab: ⚙️ Optimization) to generate the network visualization")
        
        # Show a preview of firm locations even without optimization
        st.markdown("#### 📍 Configured Firm Locations Preview")
        for firm_id in ["F1", "F2", "F3", "F4", "F5"]:
            name = st.session_state.firm_locations[firm_id]["name"]
            lat = st.session_state.firm_locations[firm_id]["lat"]
            lon = st.session_state.firm_locations[firm_id]["lon"]
            st.write(f"**{name}:** {lat:.6f}, {lon:.6f}")
    else:
        # INTERACTIVE MAP FIRST
        st.markdown("### 🗺️ Interactive Symbiosis Network Map")
        
        # Map and connections table
        col_map, col_connections_table = st.columns([2, 1])
        
        with col_map:
            st.markdown("#### 🗺️ Network Map")
            st.caption("Click on connection lines to see exchange details")
            
            # Create professional map
            firm_names_for_map = [firm_map[f"F{i+1}"] for i in range(5)]
            
            # Get active synergies from session state
            synergy_matrix = st.session_state.get("synergy_matrix")
            active_synergies = []
            if synergy_matrix is not None:
                if synergy_matrix.loc["Waste heat", "Electricity"]:
                    active_synergies.append("heat→elec")
                if synergy_matrix.loc["Plastic scrap", "Polymer"]:
                    active_synergies.append("scrap→poly")
                if synergy_matrix.loc["Steam/Wastewater", "Water"]:
                    active_synergies.append("steam→water")
            
            m = create_professional_symbiosis_map(
                df_arcs=df_qz,
                coords=coords,
                firm_names=firm_names_for_map,
                robustness_threshold=0.2,
                active_synergies=active_synergies
            )
            
            if m is not None:
                # Display map
                m.save("symbiosis_map.html")
                with open("symbiosis_map.html", "r", encoding="utf-8") as f:
                    st.components.v1.html(f.read(), height=700)
            else:
                st.warning("No exchange connections available to display")
        
        with col_connections_table:
            st.markdown("#### 📋 Active Connections")
            
            # Create connections table
            df_connections = create_connections_table(
                df_arcs=df_qz,
                firm_names=["F1", "F2", "F3", "F4", "F5"],
                robustness_threshold=0.2
            )
            
            if not df_connections.empty:
                # Display summary statistics
                st.metric("Total Connections", len(df_connections))
                
                # Count by robustness
                robust_count = len(df_connections[df_connections["Robustness %"].str.rstrip("%").astype(float) >= 70])
                st.metric("Strong Connections", robust_count)
                
                # Display table
                st.markdown("**Connection Details:**")
                st.dataframe(df_connections, width='stretch', height=600)
            else:
                st.info("No connections meet the robustness threshold")
        
        st.markdown("---")
        
        # Download options
        st.markdown("#### 📥 Export Map & Data")
        col1, col2 = st.columns(2)
        
        with col1:
            if not df_connections.empty:
                csv = df_connections.to_csv(index=False)
                st.download_button(
                    label="📊 Download Connections Table (CSV)",
                    data=csv,
                    file_name="symbiosis_connections.csv",
                    mime="text/csv",
                    width='stretch'
                )
        
        with col2:
            if m is not None:
                with open("symbiosis_map.html", "r", encoding="utf-8") as f:
                    map_html = f.read()
                st.download_button(
                    label="🗺️ Download Interactive Map (HTML)",
                    data=map_html,
                    file_name="industrial_symbiosis_map.html",
                    mime="text/html",
                    width='stretch'
                )
        
        # AI INSIGHTS SECTION
        st.markdown("---")
        st.markdown("### 🎯 AI-Powered Network Assessment")
        
        # Get stored MC results
        df_runs = st.session_state.get("mc_results", {}).get("df_runs")
        df_flags_quality = st.session_state.get("mc_results", {}).get("df_flags")
        
        if df_runs is not None and df_qz is not None:
            # Global Assessment
            st.markdown("#### ⚠️ Network Health Assessment")
            
            warnings_insights = global_warnings_and_insights(df_runs, df_flags_quality, df_qz)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔴 Warnings & Issues**")
                if warnings_insights["warnings"]:
                    for w in warnings_insights["warnings"]:
                        st.warning(w)
                else:
                    st.success("✅ No warnings detected")
            
            with col2:
                st.markdown("**💡 Strategic Insights**")
                if warnings_insights["insights"]:
                    for ins in warnings_insights["insights"]:
                        st.info(ins)
                else:
                    st.info("No strategic insights available")
        
        # AI Partnership Recommendations
        st.markdown("---")
        st.markdown("#### 🤝 AI Partnership Recommendations")
        st.caption("Smart recommendations based on robustness analysis")
        
        firm_names = [st.session_state.firm_locations[f"F{i+1}"]["name"] for i in range(5)]
        recommendations = generate_partnership_recommendations(df_qz, firm_names=firm_names)
        
        if recommendations:
            df_recommendations = pd.DataFrame(recommendations)
            
            # Filter by confidence level
            confidence_filter = st.selectbox(
                "Filter by confidence level:",
                ["All", "STRONG ✅", "MODERATE 🟡", "WEAK 🔴"],
                key="confidence_filter"
            )
            
            if confidence_filter != "All":
                df_recommendations = df_recommendations[df_recommendations["Confidence"] == confidence_filter]
            
            if not df_recommendations.empty:
                st.dataframe(
                    df_recommendations,
                    width='stretch',
                    hide_index=True,
                    height=300
                )
                
                # Summary metrics
                col_r1, col_r2, col_r3 = st.columns(3)
                with col_r1:
                    strong = len([r for r in recommendations if "STRONG" in r["Confidence"]])
                    st.metric("Strong Partnerships", strong)
                with col_r2:
                    moderate = len([r for r in recommendations if "MODERATE" in r["Confidence"]])
                    st.metric("Moderate Partnerships", moderate)
                with col_r3:
                    weak = len([r for r in recommendations if "WEAK" in r["Confidence"]])
                    st.metric("Weak Partnerships", weak)
            else:
                st.info(f"No partnerships with {confidence_filter} confidence level")
        else:
            st.warning("No recommendations available - try running optimization with more scenarios")
        
        # Data Quality Report
        st.markdown("---")
        st.markdown("#### 📊 Data Quality Assessment")
        st.caption("Evaluation of data sources and recommendations for improvement")
        
        df_flags_quality = st.session_state.get("mc_results", {}).get("df_flags")
        if df_flags_quality is not None:
            quality_report = generate_data_quality_report(df_flags_quality)
            
            if not quality_report.empty:
                st.dataframe(
                    quality_report,
                    width='stretch',
                    hide_index=True,
                    height=250
                )
                
                # Quality summary
                n_real = sum(quality_report["Priority for Data Collection"] == "LOW")
                n_estimated = sum(quality_report["Priority for Data Collection"] == "HIGH")
                
                col_q1, col_q2 = st.columns(2)
                with col_q1:
                    st.metric("Firms with Real Data", f"{n_real}/5", 
                             delta="Good" if n_real >= 3 else "Needs improvement",
                             delta_color="normal" if n_real >= 3 else "inverse")
                with col_q2:
                    st.metric("Firms with Estimated Data", f"{n_estimated}/5",
                             delta="Priority for collection" if n_estimated > 0 else "None",
                             delta_color="inverse" if n_estimated > 0 else "off")
            else:
                st.info("No data quality information available")
        
        # Robustness Scores Detail
        st.markdown("---")
        st.markdown("#### 🎯 Exchange Robustness Analysis")
        st.caption("Detailed robustness scores for all potential exchanges")
        
        robustness_scores = compute_robustness_scores(df_qz)
        if not robustness_scores.empty:
            # Add firm names for clarity
            robustness_scores["From"] = robustness_scores["i"].apply(lambda x: firm_names[int(x)])
            robustness_scores["To"] = robustness_scores["j"].apply(lambda x: firm_names[int(x)])
            
            display_cols = ["From", "To", "stream", "prob_active", "robustness_label"]
            df_rob_display = robustness_scores[display_cols].copy()
            df_rob_display = df_rob_display.rename(columns={
                "stream": "Resource",
                "prob_active": "Probability",
                "robustness_label": "Robustness"
            })
            
            st.dataframe(
                df_rob_display.style.format({"Probability": "{:.1%}"}),
                width='stretch',
                hide_index=True,
                height=350
            )
            
            # Robustness distribution
            col_rb1, col_rb2, col_rb3 = st.columns(3)
            with col_rb1:
                highly_robust = sum(robustness_scores["robustness"] > 0.9)
                st.metric("🟢 Highly Robust", highly_robust, "(>90%)")
            with col_rb2:
                moderate = sum((robustness_scores["robustness"] > 0.5) & (robustness_scores["robustness"] <= 0.9))
                st.metric("🟡 Moderate", moderate, "(50-90%)")
            with col_rb3:
                risky = sum(robustness_scores["robustness"] <= 0.5)
                st.metric("🔴 Risky", risky, "(<50%)")
        else:
            st.warning("No robustness data available")

# ============================================
# SIDEBAR: PLATFORM INFO & QUICK ACTIONS
# ============================================
with st.sidebar:
    # Display Mondragon University logo
    import os
    logo_path = "mondragon.logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width='stretch')
    else:
        st.markdown("🎓 **Mondragón Unibertsitatea**")
    
    st.markdown("---")
    
    # About section
    with st.expander("ℹ️ About This Platform", expanded=True):
        st.markdown("""
        **Industrial Symbiosis Platform**
        
        Professional tool for optimizing resource exchanges in industrial networks.
        
        **Key Features:**
        - 🏢 Individual firm management with real/EIO data
        - 📊 Dynamic synergy matrix configuration
        - 💰 Comprehensive cost parameter control
        - 🎲 Monte Carlo uncertainty analysis
        - 🤖 AI-powered recommendations
        - 🗺️ Interactive geographic visualization
        
        **Version:** 2.1
        **Last Updated:** January 2026
        """)
    
    st.markdown("---")
    
    # Platform Status
    st.markdown("### 📊 Platform Status")
    
    # Data status
    real_count = sum(st.session_state.use_real_data.values())
    if real_count == 0:
        st.info("🔢 **Data:** Full EIO Mode")
    elif real_count == 5:
        st.success("📊 **Data:** Full Real Data")
    else:
        st.warning(f"🔀 **Data:** Hybrid ({real_count}/5 real)")
    
    # Synergy status
    if "synergy_matrix" in st.session_state:
        active_synergies = int(st.session_state.synergy_matrix.sum().sum())
        if active_synergies > 0:
            st.success(f"🔄 **Synergies:** {active_synergies} active")
        else:
            st.error("⚠️ **Synergies:** None enabled")
    
    # Optimization status
    if st.session_state.get("mc_run_complete", False):
        n_scenarios = len(st.session_state.get("mc_results", {}).get("df_runs", []))
        st.success(f"✅ **Optimization:** {n_scenarios} scenarios")
    else:
        st.info("⏳ **Optimization:** Not run yet")
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Reset Data", width='stretch'):
        # Reset to default values
        st.session_state.firm_locations = {
            "F1": {"name": "Firm 1", "lat": 40.416775, "lon": -3.703790},
            "F2": {"name": "Firm 2", "lat": 40.426775, "lon": -3.713790},
            "F3": {"name": "Firm 3", "lat": 40.406775, "lon": -3.693790},
            "F4": {"name": "Firm 4", "lat": 40.436775, "lon": -3.723790},
            "F5": {"name": "Firm 5", "lat": 40.396775, "lon": -3.683790},
        }
        st.session_state.firm_supply = {
            "F1": {"Heat": 100.0, "Scrap": 50.0, "Steam": 30.0},
            "F2": {"Heat": 80.0, "Scrap": 60.0, "Steam": 25.0},
            "F3": {"Heat": 120.0, "Scrap": 40.0, "Steam": 35.0},
            "F4": {"Heat": 90.0, "Scrap": 70.0, "Steam": 28.0},
            "F5": {"Heat": 110.0, "Scrap": 55.0, "Steam": 32.0},
        }
        st.session_state.firm_demand = {
            "F1": {"Electricity": 90.0, "Water": 20.0, "Polymer": 45.0},
            "F2": {"Electricity": 70.0, "Water": 25.0, "Polymer": 55.0},
            "F3": {"Electricity": 100.0, "Water": 18.0, "Polymer": 35.0},
            "F4": {"Electricity": 80.0, "Water": 22.0, "Polymer": 65.0},
            "F5": {"Electricity": 95.0, "Water": 24.0, "Polymer": 50.0},
        }
        st.session_state.mc_run_complete = False
        st.rerun()
    
    st.markdown("---")
    
    # Quick Tips
    with st.expander("💡 Quick Tips"):
        st.markdown("""
        **Getting Started:**
        1. Configure firms in Tab 1
        2. Set synergies in Tab 2
        3. Adjust costs in Tab 3
        4. Run optimization
        
        **Pro Tips:**
        - Use real data for accurate results
        - Enable relevant synergies only
        - Test different cost scenarios
        - Export results for reports
        """)

# ============================================
# TAB 5: USER GUIDE
# ============================================
with tab5:
    # Professional Header
    st.markdown("""
    <div style='background: linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h2 style='color: white; margin: 0;'>📖 SIMBIOPTIMIZE - User Guide</h2>
        <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>
            Complete documentation for optimal resource exchange network analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Table of Contents
    st.markdown("### 📑 Table of Contents")
    toc_col1, toc_col2 = st.columns(2)
    with toc_col1:
        st.markdown("""
        1. [Platform Overview](#platform-overview)
        2. [Getting Started](#getting-started)
        3. [Workflow Guide](#workflow-guide)
        4. [Technical Glossary](#technical-glossary)
        """)
    with toc_col2:
        st.markdown("""
        5. [Use Cases](#use-cases)
        6. [FAQ](#frequently-asked-questions)
        7. [Troubleshooting](#troubleshooting)
        8. [Contact & Support](#contact-support)
        """)
    
    st.markdown("---")
    
    # Section 1: Platform Overview
    with st.expander("🎯 1. Platform Overview", expanded=True):
        st.markdown("""
        ### What is Industrial Symbiosis?
        
        **Industrial symbiosis** is a collaborative approach where companies exchange resources, energy, 
        water, and by-products to create circular economy networks. One firm's waste becomes another's 
        valuable input, reducing environmental impact and operational costs.
        
        ### What Does This Platform Do?
        
        This platform helps you:
        - 📊 **Analyze** waste streams and input demands across multiple firms
        - 🔗 **Identify** optimal resource exchange partnerships
        - 💰 **Calculate** economic benefits and costs
        - 🎲 **Simulate** uncertainty with Monte Carlo scenarios
        - 📈 **Visualize** symbiosis networks on interactive maps
        - 🚀 **Optimize** using advanced MILP (Mixed-Integer Linear Programming)
        
        ### Key Features
        
        ✅ **5-Firm Network Analysis** - Manage up to 5 industrial facilities  
        ✅ **3 Synergy Types** - Heat→Electricity, Scrap→Polymer, Steam→Water  
        ✅ **Geospatial Mapping** - Distance-based transport cost calculation  
        ✅ **Economic Optimization** - Minimize total network costs  
        ✅ **Uncertainty Handling** - Monte Carlo simulation (up to 1000 scenarios)  
        ✅ **Interactive Dashboards** - Real-time results visualization  
        
        ---
        
        ### System Architecture
        
        """)
        
        # Display Framework diagram
        framework_path = "FrameworkSI.png"
        if os.path.exists(framework_path):
            st.image(framework_path, caption="SIMBIOPTIMIZE System Architecture & Workflow", width='stretch')
        else:
            st.warning("⚠️ Framework diagram (FrameworkSI.png) not found in the project directory")
        
        st.markdown("""
        
        """)
    
    # Section 2: Getting Started
    with st.expander("🚀 2. Getting Started - Quick Start Guide"):
        st.markdown("""
        ### Prerequisites
        
        Before using the platform, ensure you have:
        - ✅ **Firm data**: Names, locations (latitude/longitude), and production data
        - ✅ **Supply data** (S): Waste heat (MWh), plastic scrap (tons), steam/wastewater (m³)
        - ✅ **Demand data** (D): Electricity (MWh), polymer (tons), water (m³) requirements
        - ✅ **Cost parameters**: Market prices for materials, disposal, transport, etc.
        
        ---
        
        ### 5-Minute Quick Start
        
        **Step 1: Configure Firms (Tab 1 - Firms Management)**
        1. Click on each **Firm 1-5** sub-tab
        2. Enter firm name and location (drag map marker or enter coordinates)
        3. Choose data source:
           - **Real Data** ✏️: Enter your actual production values
           - **EIO Model** 🔢: Use economic input-output estimates
        4. Fill in Supply (waste available) and Demand (inputs needed)
        
        **Step 2: Enable Synergies (Tab 2 - Data Matrices)**
        1. Check the synergies you want to analyze:
           - ☑️ Heat → Electricity (thermal energy recovery)
           - ☑️ Scrap → Polymer (plastic recycling)
           - ☑️ Steam → Water (wastewater reuse)
        2. Adjust **recovery rates (γ)** - efficiency of conversion processes
        3. Set **substitution limits (δ)** - maximum % of demand that can be met by recovered inputs
        
        **Step 3: Configure Costs (Tab 3 - Optimization)**
        1. Adjust 5 cost categories using sliders:
           - 🗑️ **Disposal**: Cost to dispose waste if not used
           - 🏭 **Virgin Inputs**: Market price for new materials
           - ♻️ **Recovery**: Operational cost of waste-to-resource conversion
           - 🔗 **Activation**: Fixed cost to establish each partnership
           - 🚚 **Transport**: Variable cost per unit × distance
        2. Set Monte Carlo parameters:
           - Number of scenarios (10-1000)
           - Uncertainty level (±% variation)
           - Distribution type (uniform/normal)
        
        **Step 4: Run Optimization & View Results**
        1. Click **🚀 Execute Optimization Pipeline**
        2. Wait for completion (progress bar shows status)
        3. Explore results in 5 sub-tabs:
           - **S & D Scenarios**: All generated supply/demand pairs
           - **Optimal Solutions**: Partnership frequencies and flows
           - **Statistical Analysis**: Cost distributions and variability
           - **Network Topology**: (Coming soon)
           - **Complete Data**: Full results table with export option
        
        **Step 5: Visualize Network (Tab 4 - Network Visualization)**
        1. View interactive map with:
           - Firm locations (color-coded by role)
           - Connection lines (color = synergy type, thickness = flow volume)
           - Robustness indicators (opacity = frequency %)
        2. Export map as HTML for presentations
        
        ---
        
        ### Video Tutorial
        
        **[RESERVED SPACE FOR VIDEO/GIF]**
        _You can embed a screen recording or step-by-step GIF here_
        
        """)
    
    # Section 3: Workflow Guide
    with st.expander("📋 3. Detailed Workflow Guide - Tab-by-Tab"):
        st.markdown("""
        ### Tab 1: 🏢 Firms Management
        
        **Purpose**: Configure the 5 industrial facilities in your network.
        
        **Actions**:
        - **Name & Location**: 
          - Enter descriptive firm names (e.g., "Steel Mill A", "Plastics Factory B")
          - Set coordinates by dragging map marker or typing lat/lon
          - Platform auto-calculates distances between all firms
        
        - **Data Source Selection**:
          - **Real Data** (recommended for accuracy): Use your actual monthly production data
          - **EIO Model** (for preliminary analysis): Uses economic sector averages
        
        - **Supply Matrix (S)**: 
          - Heat: Waste heat from production (MWh/month)
          - Scrap: Plastic waste generated (tons/month)
          - Steam: Wastewater or steam available (m³/month)
        
        - **Demand Matrix (D)**:
          - Electricity: Power requirements (MWh/month)
          - Polymer: Plastic resin needed (tons/month)
          - Water: Process water demand (m³/month)
        
        **Best Practices**:
        - ✅ Use consistent time periods (all monthly or all yearly)
        - ✅ Be conservative with estimates (underestimate supply, overestimate demand)
        - ✅ Verify location accuracy - distances affect transport costs significantly
        
        ---
        
        ### Tab 2: 📊 Data Matrices
        
        **Purpose**: Define which resource exchanges are technically feasible and set conversion parameters.
        
        **Synergy Activation Matrix**:
        
        | Waste Output | Can Become | Input Required | Example |
        |--------------|------------|----------------|---------|
        | Waste heat | → | Electricity | ORC turbine, heat exchanger |
        | Plastic scrap | → | Polymer | Mechanical/chemical recycling |
        | Steam/Wastewater | → | Water | Treatment, purification |
        
        **Recovery Rate (γ) - Technical Efficiency**:
        - Represents **conversion efficiency** from waste to useful input
        - γ = 0.9 means 100 MWh waste heat → 90 MWh electricity (10% loss)
        - Typical ranges:
          - Heat→Electricity: 0.15-0.35 (Carnot cycle limited)
          - Scrap→Polymer: 0.70-0.95 (mechanical recycling)
          - Steam→Water: 0.85-0.98 (treatment efficiency)
        
        **Substitution Share (δ) - Market/Technical Limits**:
        - Represents **maximum fraction** of demand met by recovered inputs
        - δ = 0.5 means recovered materials can satisfy at most 50% of total demand
        - Why limits exist:
          - Quality differences (virgin vs. recycled)
          - Regulatory requirements (food-grade polymers)
          - Process stability (baseload vs. variable heat)
        
        **Example Configuration**:
        ```
        Synergy: Heat → Electricity
        γ (recovery rate) = 0.25 (25% thermal efficiency)
        δ (substitution limit) = 0.40 (max 40% of electricity from waste heat)
        
        Interpretation: If Firm A needs 100 MWh electricity and Firm B has 
        200 MWh waste heat available, max recoverable = 200 × 0.25 = 50 MWh,
        but max allowed = 100 × 0.40 = 40 MWh → optimizer uses 40 MWh
        ```
        
        ---
        
        ### Tab 3: ⚙️ Optimization Engine
        
        **Purpose**: Run the optimization solver to find the economically optimal symbiosis network.
        
        **Cost Model Components**:
        
        The optimizer minimizes total system cost:
        
        $$
        \\min \\quad C_{\\text{total}} = C_{\\text{disposal}} + C_{\\text{virgin}} + C_{\\text{recovery}} + C_{\\text{activation}} + C_{\\text{transport}}
        $$
        
        **1. Disposal Costs (€/unit)**
        - What you pay to **get rid of** waste if not used in symbiosis
        - Higher → optimizer prefers using waste over disposing
        - Examples: Landfill fees, incineration, wastewater treatment
        
        **2. Virgin Input Costs (€/unit)**
        - Market price to **purchase new** materials from external suppliers
        - Higher → optimizer prefers waste recovery over buying virgin
        - Examples: Grid electricity tariff, virgin polymer resin price
        
        **3. Recovery Costs (€/unit)**
        - Operational cost to **convert waste into useful input**
        - Lower → makes symbiosis more economically attractive
        - Includes: Energy, labor, maintenance, consumables
        
        **4. Activation Costs (€/connection)**
        - **One-time fixed** investment to establish each partnership
        - Higher → optimizer creates fewer, larger-volume connections
        - Includes: Infrastructure (pipes, conveyors), contracts, permits, monitoring
        
        **5. Transport Costs (€/unit·km)**
        - **Variable** cost proportional to quantity × distance
        - Higher → optimizer favors geographically close partnerships
        - Calculated using Haversine formula from firm coordinates
        
        **Strategic Cost Configuration Tips**:
        
        - **To maximize waste utilization**: Increase disposal costs, decrease recovery costs
        - **To prioritize close partnerships**: Increase transport costs
        - **To encourage distributed network**: Decrease activation costs
        - **To test economic viability**: Set recovery costs just below virgin input costs
        
        **Monte Carlo Simulation Settings**:
        
        - **Number of Scenarios** (10-1000):
          - More = better statistical confidence, longer computation time
          - Recommended: 100 for initial analysis, 500 for final reports
        
        - **Uncertainty (±%)**:
          - Variation in supply/demand around base values
          - Recommended: 10% for stable industries, 25% for volatile markets
        
        - **Distribution Type**:
          - **Uniform**: All values equally likely within range
          - **Normal**: Values cluster around mean (bell curve)
        
        **Execution Process**:
        
        1. **Phase 1**: Generate N random (S,D) scenario pairs
        2. **Phase 2**: Solve MILP optimization for each scenario
        3. **Output**: Aggregate statistics + individual solutions
        
        ---
        
        ### Tab 4: 🌐 Network Visualization
        
        **Purpose**: Visualize the optimized symbiosis network on an interactive map.
        
        **Map Elements**:
        
        - **Firm Markers** (circles):
          - Size: Proportional to total resource exchange volume
          - Color: Indicates supplier/consumer role
          - Click: View firm details popup
        
        - **Connection Lines** (arcs):
          - **Color**: Synergy type (Heat=Blue, Scrap=Orange, Steam=Green)
          - **Thickness**: Average flow quantity
          - **Opacity**: Robustness (partnership frequency %)
          - **Style**: Dashed if low robustness (<50%)
        
        - **Legend**:
          - Exchange types with colors
          - Robustness scale (Strong ≥70%, Moderate 40-70%, Weak <40%)
          - Line characteristics explanation
        
        **Interpretation**:
        
        - **Thick, opaque lines** = Robust, high-volume partnerships (prioritize these!)
        - **Thin, dashed lines** = Uncertain, low-probability connections (risky)
        - **No connection** = Partnership not economically viable
        
        **Export Options**:
        - Download map as standalone HTML file
        - Share with stakeholders
        - Embed in reports/presentations
        
        """)
    
    # Section 4: Technical Glossary
    with st.expander("📚 4. Technical Glossary & Key Concepts"):
        st.markdown("""
        ### Mathematical Notation
        
        | Symbol | Name | Meaning | Units |
        |--------|------|---------|-------|
        | **S_il** | Supply matrix | Waste/by-product available from firm i, resource l | MWh, tons, m³ |
        | **D_jk** | Demand matrix | Input required by firm j, resource k | MWh, tons, m³ |
        | **q_ij** | Flow variables | Quantity exchanged from firm i to firm j | MWh, tons, m³ |
        | **z_ij** | Binary variables | Partnership activation (0=no, 1=yes) | {0, 1} |
        | **γ (gamma)** | Recovery rate | Conversion efficiency from waste to input | 0-1 (%) |
        | **δ (delta)** | Substitution share | Max % of demand met by recovered inputs | 0-1 (%) |
        | **d_ij** | Distance | Haversine distance between firms i and j | km |
        | **C_total** | Objective function | Total network cost to minimize | € |
        
        ---
        
        ### Optimization Concepts
        
        **MILP (Mixed-Integer Linear Programming)**:
        - Optimization technique combining continuous (q) and binary (z) decision variables
        - Finds global optimal solution (not heuristic)
        - Solver: CBC, GLPK, or commercial (Gurobi, CPLEX)
        
        **Constraints**:
        1. **Supply constraints**: Cannot send more waste than available
        2. **Demand constraints**: Must meet minimum input requirements
        3. **Big-M constraints**: q_ij = 0 if z_ij = 0 (no flow without active partnership)
        4. **Delta constraints**: Recovered inputs ≤ δ × Total demand
        
        **Monte Carlo Method**:
        - Generate many random scenarios by varying S and D within uncertainty bounds
        - Optimize each scenario independently
        - Aggregate results to identify robust partnerships
        
        ---
        
        ### Industrial Symbiosis Terms
        
        **Synergy**: A mutually beneficial resource exchange between two or more firms  
        **Anchor Firm**: Large facility providing substantial waste streams  
        **Eco-Industrial Park**: Geographically clustered firms optimized for symbiosis  
        **Circular Economy**: Economic system minimizing waste by reusing resources  
        **By-product**: Secondary output from production process (not main product)  
        **Virgin Material**: New, unrecycled raw material from primary sources  
        
        ---
        
        ### Data Sources
        
        **EIO (Economic Input-Output) Model**:
        - Sector-level average data from economic tables
        - Useful for preliminary/feasibility studies
        - Less accurate than real firm data
        
        **Real Data**:
        - Actual measurements from firm operations
        - Recommended for final decision-making
        - Sources: Production reports, energy audits, waste manifests
        
        """)
    
    # Section 5: Use Cases
    with st.expander("💼 5. Practical Use Cases & Examples"):
        st.markdown("""
        ### Use Case 1: Steel-Cement-Greenhouse Cluster
        
        **Scenario**: Industrial park with steel mill, cement plant, and greenhouse facility.
        
        **Synergies**:
        - Steel mill → Cement plant: Waste heat for kiln preheating
        - Steel mill → Greenhouse: Waste heat for climate control
        - Cement plant → Greenhouse: CO₂ for photosynthesis enhancement
        
        **Platform Configuration**:
        ```
        Firm 1 (Steel Mill): 
          Supply: 850 MWh heat/month
          Demand: 200 MWh electricity
        
        Firm 2 (Cement Plant):
          Supply: 320 MWh heat/month
          Demand: 150 MWh electricity
        
        Firm 3 (Greenhouse):
          Supply: 0 MWh heat
          Demand: 500 MWh heat equivalent
        
        Synergy Enabled: Heat → Electricity (γ=0.22, δ=0.35)
        Result: 187 MWh of waste heat converted to electricity
        Cost Savings: €24,500/month vs. virgin grid electricity
        ```
        
        ---
        
        ### Use Case 2: Plastics Recycling Network
        
        **Scenario**: Automotive parts manufacturer + Packaging producer + Recycling facility.
        
        **Challenge**: Automotive plant generates 45 tons/month HDPE scrap; packaging plant needs 60 tons/month HDPE resin.
        
        **Platform Analysis**:
        - Enabled synergy: Scrap → Polymer (γ=0.88, δ=0.70)
        - Optimal solution: 39.6 tons/month exchange (45 × 0.88)
        - Max allowed by delta: 42 tons (60 × 0.70)
        - Actual flow: 39.6 tons (limited by supply, not delta)
        
        **Economic Impact**:
        - Virgin polymer cost avoided: €79,200/year (39.6 tons × €2,000/ton)
        - Recovery cost: €31,680/year (39.6 tons × €800/ton processing)
        - Transport cost: €3,960/year (39.6 tons × 12 km × €8.33/ton·km)
        - Net savings: €43,560/year (55% reduction)
        
        ---
        
        ### Use Case 3: Uncertainty Analysis for Investment Decision
        
        **Scenario**: Chemical plant considering heat recovery investment; production varies ±20% seasonally.
        
        **Platform Setup**:
        - Run 500 scenarios with ±20% uncertainty
        - Monte Carlo distribution: Normal (reflects seasonal patterns)
        
        **Results**:
        - Partnership robust in 87% of scenarios (high confidence)
        - Average savings: €38,400/year (σ = €6,200)
        - Worst-case savings: €22,100/year (still profitable)
        - **Decision**: Proceed with investment (low risk)
        
        **Alternative Outcome** (if robustness was only 32%):
        - Partnership sensitive to uncertainty
        - Consider flexible/modular infrastructure
        - Negotiate long-term supply agreements
        
        """)
    
    # Section 6: FAQ
    with st.expander("❓ 6. Frequently Asked Questions (FAQ)"):
        st.markdown("""
        ### General Questions
        
        **Q: How long does optimization take?**  
        A: Depends on scenarios:
        - 10 scenarios: ~5 seconds
        - 100 scenarios: ~45 seconds
        - 500 scenarios: ~3-4 minutes
        - 1000 scenarios: ~7-10 minutes
        
        **Q: Can I add more than 5 firms?**  
        A: Current version supports exactly 5 firms. Contact developers for enterprise version with N firms.
        
        **Q: What if I don't know exact costs?**  
        A: Use industry averages or ranges, then run sensitivity analysis with different values.
        
        ---
        
        ### Data & Configuration
        
        **Q: What's the difference between EIO and Real Data?**  
        A:
        - **EIO**: Economic sector averages (e.g., "typical steel mill"). Fast but generic.
        - **Real Data**: Your actual measurements. Accurate but requires data collection.
        
        **Q: How do I get firm coordinates?**  
        A: Use Google Maps:
        1. Right-click firm location → "What's here?"
        2. Copy latitude/longitude
        3. Paste into platform
        
        **Q: What if two firms have identical locations?**  
        A: System assigns small offset (0.001°) to avoid division-by-zero in distance calculations.
        
        ---
        
        ### Optimization & Results
        
        **Q: Why did the optimizer find "no partnerships"?**  
        A: Common reasons:
        - Recovery costs > Virgin input costs (not economically viable)
        - Substitution limits (δ) set too low
        - Transport costs too high due to large distances
        - Supply far below demand (insufficient waste available)
        
        **Q: What does "Partnership Frequency = 45%" mean?**  
        A: In 45% of simulated scenarios, the optimizer activated this connection. 
        - >70% = Robust (likely to happen)
        - 40-70% = Moderate (depends on conditions)
        - <40% = Weak (uncertain, risky)
        
        **Q: Can I trust results with only 10 scenarios?**  
        A: Use 10 for quick testing only. For decisions, use ≥100 (better ≥500).
        
        **Q: Why are some q values non-zero but z=0?**  
        A: This shouldn't happen (indicates solver error). Check constraints.
        
        ---
        
        ### Technical Issues
        
        **Q: Error: "No feasible solution found"**  
        A: Constraints too restrictive:
        - Increase substitution limits (δ)
        - Check supply/demand balance
        - Verify synergies are enabled
        
        **Q: Platform is slow/freezing**  
        A: Try:
        - Reduce number of scenarios
        - Close other browser tabs
        - Use Chrome/Firefox (faster than IE/Safari)
        - Check CPU usage (optimization is compute-intensive)
        
        **Q: Map doesn't load**  
        A: Requires internet connection for map tiles. Check firewall/proxy settings.
        
        """)
    
    # Section 7: Troubleshooting
    with st.expander("🔧 7. Troubleshooting & Common Issues"):
        st.markdown("""
        ### Error Messages
        
        | Error | Cause | Solution |
        |-------|-------|----------|
        | "Please configure firm data first" | Haven't filled Tab 1 | Complete all 5 firms in Tab 1 |
        | "No synergies enabled" | Synergy matrix unchecked | Enable at least one synergy in Tab 2 |
        | "Solver failed" | Infeasible problem | Check supply/demand balance, relax constraints |
        | "Division by zero" | Two firms at same location | Adjust coordinates slightly |
        | "Invalid cost parameters" | Negative costs entered | All costs must be ≥ 0 |
        
        ---
        
        ### Performance Issues
        
        **Slow Optimization**:
        - ✅ Reduce scenarios (start with 50, increase if needed)
        - ✅ Close unnecessary browser tabs
        - ✅ Use local installation instead of cloud (if applicable)
        
        **High Memory Usage**:
        - Clear browser cache
        - Restart Streamlit session
        - Avoid running >1000 scenarios on low-RAM machines
        
        ---
        
        ### Data Validation
        
        **Unrealistic Results**:
        
        1. **All partnerships have 100% frequency**:
           - Uncertainty too low (increase ±%)
           - Symbiosis strongly profitable (verify costs)
        
        2. **Total costs are negative**:
           - Disposal costs too high or recovery costs too low
           - Check cost parameter units (€/MWh vs €/kWh)
        
        3. **No waste utilized**:
           - Virgin inputs cheaper than recovery
           - Activation costs prohibitively high
           - Distances too large (transport costs dominate)
        
        **Verification Checklist**:
        - [ ] Supply ≤ Production capacity
        - [ ] Demand ≤ Total consumption
        - [ ] Recovery rate (γ) ≤ 1.0
        - [ ] Substitution limit (δ) ≤ 1.0
        - [ ] All costs in same currency
        - [ ] Coordinates within valid range (lat: -90 to 90, lon: -180 to 180)
        
        """)
    
    # Section 8: Contact & Support
    with st.expander("📞 8. Contact & Support"):
        st.markdown("""
        ### Technical Support
        
        **Platform Developers**:
        - 🏛️ **Institution**: Mondragón Unibertsitatea
        - 👤 **Developer**: Oscar Nieto-Cerezo
        - 🌐 **Website**: [www.mondragon.edu](https://www.mondragon.edu)
        - 📧 **Email**: [onieto@mondragon.edu](mailto:onieto@mondragon.edu)
        
        ---
        
        ### Reporting Issues
        
        When reporting bugs, please include:
        1. **Error message** (exact text or screenshot)
        2. **Steps to reproduce** (what you clicked/entered)
        3. **Browser & OS** (Chrome on Windows, Firefox on Mac, etc.)
        4. **Input data** (if relevant - you can export from Tab 1)
        
        ---
        
        ### Feature Requests
        
        Have ideas for improvements? We'd love to hear:
        - Additional synergy types
        - More firms (>5)
        - Multi-period optimization
        - Environmental impact metrics (CO₂, water savings)
        - Advanced visualization options
        
        ---
        
        ### Resources & Documentation
        
        **Academic Publications**:
        - [Link to research papers on industrial symbiosis]
        - [Link to optimization methodology papers]
        
        **External Tools**:
        - **EIO Data**: [EXIOBASE](https://www.exiobase.eu/)
        - **GIS Coordinates**: [Google Maps](https://www.google.com/maps)
        - **Cost Data**: Industry reports, government statistics
        
        **Training Materials**:
        - **Video Tutorials**: [YouTube playlist - to be added]
        - **Sample Datasets**: [Download examples - to be added]
        - **Case Studies**: [Real-world applications - to be added]
        
        """)
    
    # Quick Reference Card
    st.markdown("---")
    st.markdown("### 📌 Quick Reference Card")
    
    ref_col1, ref_col2, ref_col3 = st.columns(3)
    
    with ref_col1:
        st.markdown("""
        **🔢 Key Variables**
        - **S**: Supply (waste available)
        - **D**: Demand (inputs needed)
        - **q**: Flow quantities
        - **z**: Partnership on/off
        - **γ**: Recovery efficiency
        - **δ**: Substitution limit
        """)
    
    with ref_col2:
        st.markdown("""
        **💰 Cost Components**
        1. Disposal (get rid of waste)
        2. Virgin (buy new materials)
        3. Recovery (convert waste)
        4. Activation (infrastructure)
        5. Transport (shipping)
        """)
    
    with ref_col3:
        st.markdown("""
        **✅ Workflow Checklist**
        - [ ] Configure 5 firms (Tab 1)
        - [ ] Enable synergies (Tab 2)
        - [ ] Set costs & scenarios (Tab 3)
        - [ ] Run optimization
        - [ ] View map & export (Tab 4)
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem; padding: 2rem;'>
        <p><strong>SIMBIOPTIMIZE v1.0</strong></p>
        <p>Developed by Mondragón Unibertsitatea | Powered by Streamlit, Folium, PuLP</p>
        <p>© 2026 - All Rights Reserved</p>
    </div>
    """, unsafe_allow_html=True)
