"""
Clutch Teams Analysis Page
Analyze team performance under different pressure scenarios
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.visualizations import COLORS
from src.utils.data_cache import get_processed_data
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Pressure Index ranges for analysis
PI_RANGES = [
    (0.0, 0.5, "0.0-0.5"),
    (0.5, 0.75, "0.5-0.75"),
    (0.75, 1.0, "0.75-1.0"),
    (1.0, 1.25, "1.0-1.25"),
    (1.25, 1.5, "1.25-1.5"),
    (1.5, 1.75, "1.5-1.75"),
    (1.75, 2.0, "1.75-2.0"),
    (2.0, 2.25, "2.0-2.25"),
    (2.25, 2.5, "2.25-2.5"),
    (2.5, 2.75, "2.5-2.75"),
    (2.75, 3.0, "2.75-3.0"),
    (3.0, 3.25, "3.0-3.25"),
    (3.25, 3.5, "3.25-3.5"),
    (3.5, 100.0, ">3.5"),
]

# Phase definitions (in balls)
PHASES = {
    'powerplay': (0, 36, 'Powerplay (0-6 overs)'),
    'middle_overs': (37, 96, 'Middle Overs (7-16 overs)'),
    'death_overs': (97, 120, 'Death Overs (17-20 overs)')
}


# Removed get_csv_path() - now using load_csv_data() from csv_loader


def calculate_team_stats(df: pd.DataFrame, phase_key: str, pi_range: tuple) -> dict:
    """
    Calculate team performance statistics for a specific phase and PI range

    Args:
        df: DataFrame with team data
        phase_key: Phase identifier ('powerplay', 'middle_overs', 'death_overs')
        pi_range: Tuple of (min_pi, max_pi, label)

    Returns:
        Dictionary with calculated statistics
    """
    phase_min, phase_max, _ = PHASES[phase_key]
    pi_min, pi_max, pi_label = pi_range

    # Filter data for phase and PI range
    filtered = df[
        (df['ball'] > phase_min) &
        (df['ball'] <= phase_max) &
        (df['pressure_index'] >= pi_min) &
        (df['pressure_index'] < pi_max)
    ]

    if len(filtered) == 0:
        return {
            'balls_faced': 0,
            'runs_scored': 0,
            'wickets_lost': 0,
            'team_strike_rate': 0.0,
            'run_rate': 0.0,
            'boundary_rate': 0.0,
            'wicket_rate': 0.0,
            'win_rate': 0.0,
            'avg_pi': 0.0
        }

    balls_faced = len(filtered)
    runs_scored = filtered['runs_scored'].sum()
    wickets_lost = filtered['is_wicket'].sum()
    boundaries = filtered[filtered['runs_scored'].isin([4, 6])]['runs_scored'].count()

    # Group by match to calculate win rate using the 'winner' column
    matches = filtered.groupby('match_id').agg({
        'winner': 'first',  # Winner of the match
        'team': 'first'  # Team batting
    })

    # Win if the team equals the winner
    wins = (matches['team'] == matches['winner']).sum()
    total_matches = len(matches)
    win_rate = (wins / total_matches * 100) if total_matches > 0 else 0

    team_strike_rate = (runs_scored / balls_faced * 100) if balls_faced > 0 else 0
    run_rate = (runs_scored / balls_faced * 6) if balls_faced > 0 else 0  # Runs per over
    boundary_rate = (boundaries / balls_faced * 100) if balls_faced > 0 else 0
    wicket_rate = (wickets_lost / balls_faced * 100) if balls_faced > 0 else 0

    avg_pi = filtered['pressure_index'].mean()

    return {
        'balls_faced': balls_faced,
        'runs_scored': runs_scored,
        'wickets_lost': wickets_lost,
        'matches': total_matches,
        'wins': wins,
        'team_strike_rate': round(team_strike_rate, 2),
        'run_rate': round(run_rate, 2),
        'boundary_rate': round(boundary_rate, 2),
        'wicket_rate': round(wicket_rate, 2),
        'win_rate': round(win_rate, 2),
        'avg_pi': round(avg_pi, 2)
    }


def render_clutch_teams():
    """Render the Clutch Teams analysis page"""

    try:
        # Load pre-processed data from cache
        with st.spinner("Loading dataset..."):
            df = get_processed_data()

        # Add cumulative runs and wickets for win rate calculation
        df['runs'] = df['runs_scored_cumulative']
        df['wickets'] = df.get('inns_wkts', df.get('wickets_lost', 0))

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return

    st.markdown("---")

    # Tabs for different analyses
    tab1, tab2 = st.tabs(["Individual Team Stats", "Team Comparison"])

    with tab1:
        render_individual_team_stats(df)

    with tab2:
        render_team_comparison(df)


def render_individual_team_stats(df: pd.DataFrame):
    """Render individual team statistics section"""

    st.markdown("### Individual Team Analysis")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        # Team selection
        teams = sorted(df['team'].dropna().unique())
        selected_team = st.selectbox("Select Team", teams, key="team_ind_team")

    with col2:
        # Opposition filter
        oppositions = ['All'] + sorted(df['opposition'].dropna().unique().tolist())
        selected_opposition = st.selectbox("Opposition", oppositions, key="team_ind_opp")

    with col3:
        # Venue filter
        venues = ['All'] + sorted(df['venue'].dropna().unique().tolist())
        selected_venue = st.selectbox("Venue", venues, key="team_ind_venue")

    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        min_date = df['date'].min().date() if not df['date'].isna().all() else datetime.now().date() - timedelta(days=365)
        start_date = st.date_input("Start Date", min_date, key="team_ind_start")

    with col2:
        max_date = df['date'].max().date() if not df['date'].isna().all() else datetime.now().date()
        end_date = st.date_input("End Date", max_date, key="team_ind_end")

    # Apply filters
    filtered_df = df[df['team'] == selected_team].copy()

    if selected_opposition != 'All':
        filtered_df = filtered_df[filtered_df['opposition'] == selected_opposition]

    if selected_venue != 'All':
        filtered_df = filtered_df[filtered_df['venue'] == selected_venue]

    filtered_df = filtered_df[
        (filtered_df['date'] >= pd.to_datetime(start_date)) &
        (filtered_df['date'] <= pd.to_datetime(end_date))
    ]

    if len(filtered_df) == 0:
        st.warning("No data available for selected filters")
        return

    st.markdown("---")

    # Display stats for each phase
    for phase_key, (phase_min, phase_max, phase_name) in PHASES.items():
        st.markdown(f"#### {phase_name}")

        # Calculate stats for each PI range
        stats_data = []
        for pi_range in PI_RANGES:
            stats = calculate_team_stats(filtered_df, phase_key, pi_range)
            if stats['balls_faced'] > 0:  # Only include ranges with data
                stats_data.append({
                    'PI Range': pi_range[2],
                    'Matches': stats['matches'],
                    'Wins': stats['wins'],
                    'Win %': stats['win_rate'],
                    'Balls': stats['balls_faced'],
                    'Runs': stats['runs_scored'],
                    'Wickets': stats['wickets_lost'],
                    'Run Rate': stats['run_rate'],
                    'Boundary %': stats['boundary_rate'],
                    'Wicket Rate': stats['wicket_rate'],
                    'Avg PI': stats['avg_pi']
                })

        if stats_data:
            stats_df = pd.DataFrame(stats_data)

            # Style the dataframe
            styled_df = stats_df.style.background_gradient(
                subset=['Win %'],
                cmap='RdYlGn',
                vmin=0,
                vmax=100
            ).background_gradient(
                subset=['Run Rate'],
                cmap='Blues',
                vmin=0,
                vmax=12
            ).format({
                'Win %': '{:.2f}',
                'Run Rate': '{:.2f}',
                'Boundary %': '{:.2f}',
                'Wicket Rate': '{:.2f}',
                'Avg PI': '{:.2f}'
            })

            st.dataframe(styled_df, use_container_width=True, height=400)

            # Visualization
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Win Rate by PI Range', 'Run Rate by PI Range'),
                specs=[[{"type": "bar"}, {"type": "bar"}]]
            )

            fig.add_trace(
                go.Bar(
                    x=stats_df['PI Range'],
                    y=stats_df['Win %'],
                    name='Win %',
                    marker_color=COLORS['target_zone'],
                    text=stats_df['Win %'],
                    texttemplate='%{text:.1f}%',
                    textposition='outside'
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Bar(
                    x=stats_df['PI Range'],
                    y=stats_df['Run Rate'],
                    name='Run Rate',
                    marker_color=COLORS['pressure_line'],
                    text=stats_df['Run Rate'],
                    texttemplate='%{text:.1f}',
                    textposition='outside'
                ),
                row=1, col=2
            )

            fig.update_layout(
                height=400,
                showlegend=False,
                plot_bgcolor=COLORS['card_bg'],
                paper_bgcolor=COLORS['background'],
                font=dict(color=COLORS['text']),
                xaxis=dict(tickangle=-45),
                xaxis2=dict(tickangle=-45)
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No data available for {phase_name}")

        st.markdown("---")


def render_team_comparison(df: pd.DataFrame):
    """Render team comparison section"""

    st.markdown("### Team Comparison")

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Select Teams to Compare (2-4 teams)**")
        teams = sorted(df['team'].dropna().unique())
        selected_teams = st.multiselect(
            "Teams",
            teams,
            max_selections=4,
            key="team_comp_teams"
        )

    with col2:
        # Phase selection
        phase_options = {v[2]: k for k, v in PHASES.items()}
        selected_phase_name = st.selectbox(
            "Select Phase",
            list(phase_options.keys()),
            key="team_comp_phase"
        )
        selected_phase = phase_options[selected_phase_name]

    if len(selected_teams) < 2:
        st.info("Please select at least 2 teams to compare")
        return

    # Additional filters
    col1, col2 = st.columns(2)

    with col1:
        oppositions = ['All'] + sorted(df['opposition'].dropna().unique().tolist())
        selected_opposition = st.selectbox("Opposition", oppositions, key="team_comp_opp")

    with col2:
        venues = ['All'] + sorted(df['venue'].dropna().unique().tolist())
        selected_venue = st.selectbox("Venue", venues, key="team_comp_venue")

    # Date range
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    min_date = df['date'].min().date() if not df['date'].isna().all() else datetime.now().date() - timedelta(days=365)
    max_date = df['date'].max().date() if not df['date'].isna().all() else datetime.now().date()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", min_date, key="team_comp_start")
    with col2:
        end_date = st.date_input("End Date", max_date, key="team_comp_end")

    st.markdown("---")

    # Prepare comparison data
    comparison_data = []

    for team in selected_teams:
        # Filter data
        team_df = df[df['team'] == team].copy()

        if selected_opposition != 'All':
            team_df = team_df[team_df['opposition'] == selected_opposition]

        if selected_venue != 'All':
            team_df = team_df[team_df['venue'] == selected_venue]

        team_df = team_df[
            (team_df['date'] >= pd.to_datetime(start_date)) &
            (team_df['date'] <= pd.to_datetime(end_date))
        ]

        # Calculate stats for each PI range
        for pi_range in PI_RANGES:
            stats = calculate_team_stats(team_df, selected_phase, pi_range)
            if stats['balls_faced'] > 0:
                comparison_data.append({
                    'Team': team,
                    'PI Range': pi_range[2],
                    'Matches': stats['matches'],
                    'Wins': stats['wins'],
                    'Win %': stats['win_rate'],
                    'Run Rate': stats['run_rate'],
                    'Boundary %': stats['boundary_rate'],
                    'Wicket Rate': stats['wicket_rate']
                })

    if not comparison_data:
        st.warning("No data available for selected filters")
        return

    comp_df = pd.DataFrame(comparison_data)

    # Display comparison table
    st.markdown(f"#### Comparison for {selected_phase_name}")

    # Pivot for better visualization
    pivot_df = comp_df.pivot(index='PI Range', columns='Team', values='Win %')

    styled_pivot = pivot_df.style.background_gradient(
        cmap='RdYlGn',
        axis=None,
        vmin=0,
        vmax=100
    ).format('{:.2f}')

    st.markdown("**Win Rate Comparison**")
    st.dataframe(styled_pivot, use_container_width=True)

    # Visualization - Win Rate Comparison
    fig = go.Figure()

    colors = [COLORS['pressure_line'], COLORS['target_zone'], COLORS['acceptable_zone'], COLORS['risky_zone']]

    for idx, team in enumerate(selected_teams):
        team_data = comp_df[comp_df['Team'] == team]
        fig.add_trace(go.Bar(
            x=team_data['PI Range'],
            y=team_data['Win %'],
            name=team,
            marker_color=colors[idx % len(colors)],
            text=team_data['Win %'],
            texttemplate='%{text:.1f}%',
            textposition='outside'
        ))

    fig.update_layout(
        title=f"Win Rate Comparison - {selected_phase_name}",
        xaxis_title="Pressure Index Range",
        yaxis_title="Win Rate (%)",
        barmode='group',
        height=500,
        plot_bgcolor=COLORS['card_bg'],
        paper_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        legend=dict(
            bgcolor='rgba(17, 28, 50, 0.8)',
            bordercolor=COLORS['grid'],
            borderwidth=1
        ),
        xaxis=dict(tickangle=-45)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Run Rate Comparison
    st.markdown("---")
    st.markdown("**Run Rate Comparison**")

    pivot_rr = comp_df.pivot(index='PI Range', columns='Team', values='Run Rate')
    styled_rr = pivot_rr.style.background_gradient(
        cmap='Blues',
        axis=None,
        vmin=0,
        vmax=12
    ).format('{:.2f}')

    st.dataframe(styled_rr, use_container_width=True)

    # Run Rate visualization
    fig2 = go.Figure()

    for idx, team in enumerate(selected_teams):
        team_data = comp_df[comp_df['Team'] == team]
        fig2.add_trace(go.Scatter(
            x=team_data['PI Range'],
            y=team_data['Run Rate'],
            name=team,
            mode='lines+markers',
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=8)
        ))

    fig2.update_layout(
        title=f"Run Rate Comparison - {selected_phase_name}",
        xaxis_title="Pressure Index Range",
        yaxis_title="Run Rate (runs per over)",
        height=500,
        plot_bgcolor=COLORS['card_bg'],
        paper_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        legend=dict(
            bgcolor='rgba(17, 28, 50, 0.8)',
            bordercolor=COLORS['grid'],
            borderwidth=1
        ),
        xaxis=dict(tickangle=-45)
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Detailed comparison table
    st.markdown("---")
    st.markdown("**Detailed Statistics**")

    # Format and display full comparison
    display_df = comp_df.copy()
    styled_comp = display_df.style.background_gradient(
        subset=['Win %'],
        cmap='RdYlGn',
        vmin=0,
        vmax=100
    ).background_gradient(
        subset=['Run Rate'],
        cmap='Blues',
        vmin=0,
        vmax=12
    ).format({
        'Win %': '{:.2f}',
        'Run Rate': '{:.2f}',
        'Boundary %': '{:.2f}',
        'Wicket Rate': '{:.2f}'
    })

    st.dataframe(styled_comp, use_container_width=True, height=500)


if __name__ == "__main__":
    render_clutch_teams()
