"""
UI Components Module
Reusable Streamlit components for the Pressure Index app
"""

import streamlit as st
from typing import Dict, Optional, List

# Color scheme
COLORS = {
    'background': '#0a1628',
    'card_bg': '#111c32',
    'text': '#e2e8f0',
    'text_secondary': '#94a3b8',
    'target_zone': '#10b981',
    'acceptable_zone': '#f59e0b',
    'risky_zone': '#ef4444',
    'avoid_zone': '#dc2626',
    'accent': '#06b6d4',
    'border': '#1e3a5f',
}


def apply_custom_css():
    """Apply custom CSS styling to match the Base44 app design"""
    st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background-color: #0a1628;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #111c32;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #e2e8f0 !important;
        }
        
        /* Text */
        p, span, label {
            color: #94a3b8;
        }
        
        /* Cards */
        .card {
            background-color: #111c32;
            border: 1px solid #1e3a5f;
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
        }
        
        /* Match header card */
        .match-header {
            background: linear-gradient(135deg, #111c32 0%, #1a2744 100%);
            border: 1px solid #1e3a5f;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .match-title {
            color: #e2e8f0;
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .match-subtitle {
            color: #94a3b8;
            font-size: 14px;
        }
        
        /* Stats cards */
        .stats-container {
            display: flex;
            gap: 16px;
            margin: 20px 0;
        }
        
        .stat-card {
            background-color: #111c32;
            border: 1px solid #1e3a5f;
            border-radius: 12px;
            padding: 16px;
            flex: 1;
            text-align: center;
        }
        
        .stat-label {
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-value {
            color: #e2e8f0;
            font-size: 28px;
            font-weight: 700;
            margin: 8px 0;
        }
        
        .stat-sublabel {
            color: #64748b;
            font-size: 11px;
        }
        
        /* PI specific styles */
        .pi-target { color: #10b981; }
        .pi-acceptable { color: #f59e0b; }
        .pi-risky { color: #ef4444; }
        .pi-high { color: #dc2626; }
        
        /* Zone cards */
        .zone-card {
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
        }
        
        .zone-target {
            background-color: rgba(16, 185, 129, 0.15);
            border: 1px solid #10b981;
        }
        
        .zone-acceptable {
            background-color: rgba(245, 158, 11, 0.15);
            border: 1px solid #f59e0b;
        }
        
        .zone-risky {
            background-color: rgba(239, 68, 68, 0.15);
            border: 1px solid #ef4444;
        }
        
        .zone-title {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }
        
        .zone-title-target { color: #10b981; }
        .zone-title-acceptable { color: #f59e0b; }
        .zone-title-risky { color: #ef4444; }
        
        .zone-runs {
            font-size: 20px;
            font-weight: 700;
            color: #e2e8f0;
        }
        
        .zone-rpo {
            font-size: 12px;
            color: #94a3b8;
        }
        
        /* Strategy box */
        .strategy-box {
            background: linear-gradient(135deg, #1e3a5f 0%, #111c32 100%);
            border-left: 4px solid #3b82f6;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        }
        
        .strategy-label {
            color: #f59e0b;
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .strategy-text {
            color: #e2e8f0;
            font-size: 14px;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 24px 0;
            border-top: 1px solid #1e3a5f;
            margin-top: 40px;
        }
        
        .footer-text {
            color: #94a3b8;
            font-size: 14px;
        }
        
        .footer-links {
            display: flex;
            justify-content: center;
            gap: 16px;
            margin-top: 12px;
        }
        
        .footer-link {
            color: #94a3b8;
            text-decoration: none;
            transition: color 0.2s;
        }
        
        .footer-link:hover {
            color: #06b6d4;
        }
        
        /* Input fields */
        .stTextInput > div > div > input {
            background-color: #111c32;
            border: 1px solid #1e3a5f;
            color: #e2e8f0;
        }
        
        .stSelectbox > div > div {
            background-color: #111c32;
            border: 1px solid #1e3a5f;
        }

        /* Selectbox dropdown options */
        .stSelectbox [data-baseweb="select"] > div {
            background-color: #111c32;
        }

        /* Selected option in dropdown */
        [data-baseweb="select"] [aria-selected="true"] {
            background-color: #0c1e3d !important;
            color: #ffffff !important;
        }

        /* Hover state for dropdown options */
        [data-baseweb="select"] li:hover {
            background-color: #0c1e3d !important;
            color: #ffffff !important;
        }

        /* Multi-select selected items */
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #0c1e3d !important;
            color: #ffffff !important;
        }

        /* Radio button selected */
        .stRadio [data-baseweb="radio"] input:checked + div {
            background-color: #0c1e3d !important;
            border-color: #0c1e3d !important;
        }

        /* Date input selected date */
        .stDateInput [data-baseweb="calendar"] [aria-selected="true"] {
            background-color: #0c1e3d !important;
            color: #ffffff !important;
        }

        /* Slider active thumb */
        .stSlider [role="slider"]:focus {
            box-shadow: 0 0 0 3px rgba(12, 30, 61, 0.5) !important;
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #0891b2 0%, #2563eb 100%);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #111c32;
            border: 1px solid #1e3a5f;
            border-radius: 8px;
            color: #94a3b8;
            padding: 10px 24px;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
            color: white;
            border: none;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            color: #e2e8f0 !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
        }
        
        /* Info boxes */
        .stAlert {
            background-color: #111c32;
            border: 1px solid #1e3a5f;
        }
        
        /* Dataframes */
        .stDataFrame {
            background-color: #111c32;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
    </style>
    """, unsafe_allow_html=True)


def render_match_header(team1: str, team2: str, target: Optional[int] = None, 
                       venue: str = "", competition: str = ""):
    """Render the match header card"""
    st.markdown(f"""
    <div class="match-header">
        <div class="match-title">{team1} vs {team2}</div>
        {f'<div class="match-subtitle">Target: {target}</div>' if target else ''}
        {f'<div class="match-subtitle">{venue}</div>' if venue else ''}
        {f'<div class="match-subtitle">{competition}</div>' if competition else ''}
    </div>
    """, unsafe_allow_html=True)


def render_stats_row(stats: List[Dict]):
    """
    Render a row of stat cards
    
    Args:
        stats: List of dicts with 'label', 'value', and optional 'sublabel', 'color'
    """
    cols = st.columns(len(stats))
    
    for col, stat in zip(cols, stats):
        with col:
            color_class = stat.get('color_class', '')
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">{stat['label']}</div>
                <div class="stat-value {color_class}">{stat['value']}</div>
                {f'<div class="stat-sublabel">{stat.get("sublabel", "")}</div>' if stat.get("sublabel") else ''}
            </div>
            """, unsafe_allow_html=True)


def render_pi_display(pi_value: float, phase: str = "Middle Overs"):
    """Render the main PI display with appropriate coloring"""
    if pi_value < 0.5:
        color_class = "pi-target"
        zone_label = "Target Zone"
    elif pi_value < 1.5:
        color_class = "pi-acceptable"
        zone_label = "Acceptable"
    elif pi_value < 3.5:
        color_class = "pi-risky"
        zone_label = "Risky"
    else:
        color_class = "pi-high"
        zone_label = "High Pressure"
    
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Pressure Index</div>
        <div class="stat-value {color_class}">{pi_value:.2f}</div>
        <div class="stat-sublabel {color_class}">{zone_label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_zone_projection(zone: str, runs: Optional[int], rpo: Optional[float],
                          achievable: bool = True, balls: int = 6, wickets: Optional[int] = None):
    """Render a zone projection card"""
    zone_classes = {
        'target': ('zone-target', 'zone-title-target'),
        'acceptable': ('zone-acceptable', 'zone-title-acceptable'),
        'risky': ('zone-risky', 'zone-title-risky')
    }

    zone_class, title_class = zone_classes.get(zone, ('zone-risky', 'zone-title-risky'))
    zone_name = zone.replace('_', ' ').title() + ' Zone'

    if achievable and runs is not None:
        wickets_text = f" (max {wickets} wkt{'s' if wickets != 1 else ''})" if wickets is not None else ""
        html_content = f"""
    <div class="zone-card {zone_class}">
        <div class="zone-title {title_class}">
            <span>{zone_name}</span>
        </div>
        <div class="zone-runs">{runs} runs{wickets_text}</div>
        <div class="zone-rpo">@ {rpo:.2f} RPO</div>
    </div>
    """
    else:
        html_content = f"""
    <div class="zone-card {zone_class}">
        <div class="zone-title {title_class}">
            <span>{zone_name}</span>
        </div>
        <div class="zone-rpo">Not achievable</div>
    </div>
    """

    st.markdown(html_content, unsafe_allow_html=True)


def render_projections_section(projections: Dict):
    """Render the strategic projections section"""
    st.markdown("### Strategic Projections")
    
    for horizon_key, horizon_data in projections.get('horizons', {}).items():
        balls = horizon_data.get('balls', 6)
        overs = balls // 6
        label = f"Next {overs} Over{'s' if overs > 1 else ''} ({balls} balls)"
        
        st.markdown(f"**{label}**")
        
        cols = st.columns(3)
        zones = horizon_data.get('zones', {})
        
        for col, zone in zip(cols, ['target', 'acceptable', 'risky']):
            with col:
                zone_data = zones.get(zone, {})
                render_zone_projection(
                    zone=zone,
                    runs=zone_data.get('runs'),
                    rpo=zone_data.get('rpo'),
                    achievable=zone_data.get('achievable', False),
                    balls=balls
                )


def render_strategy_tip(text: str):
    """Render a strategy tip box"""
    st.markdown(f"""
    <div class="strategy-box">
        <div class="strategy-label">Strategy:</div>
        <div class="strategy-text">{text}</div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the page footer with developer info and social links"""
    st.markdown("""
    <div class="footer">
        <div class="footer-text">Developed by Rhitankar Bandyopadhyay</div>
        <div class="footer-links">
            <a href="https://x.com/rhitankar?s=21" target="_blank" class="footer-link" title="Twitter/X">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
            </a>
            <a href="https://github.com/rhitankar8616" target="_blank" class="footer-link" title="GitHub">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
            </a>
            <a href="https://www.linkedin.com/in/rhitankar-bandyopadhyay-a2099227b/" target="_blank" class="footer-link" title="LinkedIn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                </svg>
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_no_data_message(message: str = "No data available"):
    """Render a styled no data message"""
    st.markdown(f"""
    <div class="card" style="text-align: center; padding: 40px;">
        <div style="color: #94a3b8; font-size: 16px;">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def render_loading_message(message: str = "Loading..."):
    """Render a styled loading message"""
    st.markdown(f"""
    <div class="card" style="text-align: center; padding: 40px;">
        <div style="color: #06b6d4; font-size: 16px;">{message}</div>
    </div>
    """, unsafe_allow_html=True)
