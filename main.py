"""
T20 Pressure Index Application
Main entry point for the Streamlit app

Authors: Rhitankar Bandyopadhyay & Dibyojyoti Bhattacharjee
Based on: "Applications of higher order Markov models and Pressure Index 
          to strategize controlled run chases in Twenty20 cricket"
"""

import streamlit as st
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pages.live_tracker import render_live_tracker
from src.pages.past_matches import render_past_matches
from src.pages.clutch_players import render_clutch_players
from src.pages.clutch_teams import render_clutch_teams
from src.pages.how_it_works import render_how_it_works
from src.components.ui_components import apply_custom_css, render_footer

# Page configuration
st.set_page_config(
    page_title="T20 Pressure Index",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply custom CSS
apply_custom_css()

def main():
    """Main application entry point"""
    
    # App Header
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 10px 0;">
        <h1 style="color: #f8fafc; font-size: 2.8rem; font-weight: 700; margin-bottom: 8px;">
            T20 Pressure Index
        </h1>
        <p style="color: #94a3b8; font-size: 1.1rem; margin: 0;">
            Real-time pressure quantification for T20 cricket run chases
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation Tabs
    tab_labels = ["Live PI Tracker", "Past Matches", "Clutch Players", "Clutch Teams", "How It Works"]

    # Create custom tab styling
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background-color: #111c32;
        border-radius: 12px;
        padding: 6px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 500;
        font-size: 0.95rem;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0c1e3d !important;
        color: #ffffff !important;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #f8fafc;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 24px;
    }
    </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

    with tab1:
        render_live_tracker()

    with tab2:
        render_past_matches()

    with tab3:
        render_clutch_players()

    with tab4:
        render_clutch_teams()

    with tab5:
        render_how_it_works()
    
    # Footer
    render_footer()


if __name__ == "__main__":
    main()
