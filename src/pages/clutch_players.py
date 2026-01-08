"""
Clutch Players Analysis Page
Analyze individual player performance under different pressure scenarios
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


def calculate_player_stats(df: pd.DataFrame, phase_key: str, pi_range: tuple) -> dict:
    """
    Calculate player performance statistics for a specific phase and PI range

    Args:
        df: DataFrame with player data
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
            'wickets': 0,
            'matches': 0,
            'wins': 0,
            'match_win_rate': 0.0,
            'strike_rate': 0.0,
            'avg_runs_per_ball': 0.0,
            'boundary_rate': 0.0,
            'dot_ball_rate': 0.0,
            'success_rate': 0.0,
            'avg_pi': 0.0
        }

    balls_faced = len(filtered)
    runs_scored = filtered['runs_scored'].sum()
    wickets = filtered['is_wicket'].sum()
    boundaries = filtered[filtered['runs_scored'].isin([4, 6])]['runs_scored'].count()
    dot_balls = filtered[filtered['runs_scored'] == 0]['runs_scored'].count()

    strike_rate = (runs_scored / balls_faced * 100) if balls_faced > 0 else 0
    avg_runs_per_ball = runs_scored / balls_faced if balls_faced > 0 else 0
    boundary_rate = (boundaries / balls_faced * 100) if balls_faced > 0 else 0
    dot_ball_rate = (dot_balls / balls_faced * 100) if balls_faced > 0 else 0

    # Calculate match win percentage for the player
    # Group by match to see which matches the player contributed to
    if 'match_id' in filtered.columns and 'winner' in filtered.columns and 'team' in filtered.columns:
        matches = filtered.groupby('match_id').agg({
            'winner': 'first',
            'team': 'first'
        })
        wins = (matches['team'] == matches['winner']).sum()
        total_matches = len(matches)
        match_win_rate = (wins / total_matches) if total_matches > 0 else 0
    else:
        match_win_rate = 0.5  # Default if columns not available

    # Success rate: weighted combination of match wins, survival, and performance
    # 50% weight to match win rate (most important - did the team win?)
    # 30% weight to survival (did player avoid getting out?)
    # 20% weight to strike rate (did player score runs efficiently?)

    dismissal_rate = (wickets / balls_faced) if balls_faced > 0 else 0
    survival_rate = 1 - dismissal_rate

    # Normalize strike rate to 0-1 scale (assuming 150 SR is excellent in pressure situations)
    normalized_sr = min(strike_rate / 150, 1.0)

    success_rate = (match_win_rate * 0.5 + survival_rate * 0.3 + normalized_sr * 0.2) * 100

    avg_pi = filtered['pressure_index'].mean()

    return {
        'balls_faced': balls_faced,
        'runs_scored': runs_scored,
        'wickets': wickets,
        'matches': total_matches if 'match_id' in filtered.columns else 0,
        'wins': wins if 'match_id' in filtered.columns else 0,
        'match_win_rate': round(match_win_rate * 100, 2),
        'strike_rate': round(strike_rate, 2),
        'avg_runs_per_ball': round(avg_runs_per_ball, 2),
        'boundary_rate': round(boundary_rate, 2),
        'dot_ball_rate': round(dot_ball_rate, 2),
        'success_rate': round(success_rate, 2),
        'avg_pi': round(avg_pi, 2)
    }


def render_clutch_players():
    """Render the Clutch Players analysis page"""

    try:
        # Load pre-processed data from cache
        with st.spinner("Loading dataset..."):
            df = get_processed_data()

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return

    st.markdown("---")

    # Tabs for different analyses
    tab1, tab2 = st.tabs(["Individual Player Stats", "Player Comparison"])

    with tab1:
        render_individual_player_stats(df)

    with tab2:
        render_player_comparison(df)


def render_individual_player_stats(df: pd.DataFrame):
    """Render individual player statistics section"""

    st.markdown("### Individual Player Analysis")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Player selection
        players = sorted(df['batsman'].dropna().unique())
        selected_player = st.selectbox("Select Player", players, key="player_ind_player")

    with col2:
        # Team filter
        teams = ['All'] + sorted(df['team'].dropna().unique().tolist())
        selected_team = st.selectbox("Team", teams, key="player_ind_team")

    with col3:
        # Opposition filter
        oppositions = ['All'] + sorted(df['opposition'].dropna().unique().tolist())
        selected_opposition = st.selectbox("Opposition", oppositions, key="player_ind_opp")

    with col4:
        # Venue filter
        venues = ['All'] + sorted(df['venue'].dropna().unique().tolist())
        selected_venue = st.selectbox("Venue", venues, key="player_ind_venue")

    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        min_date = df['date'].min().date() if not df['date'].isna().all() else datetime.now().date() - timedelta(days=365)
        start_date = st.date_input("Start Date", min_date, key="player_ind_start")

    with col2:
        max_date = df['date'].max().date() if not df['date'].isna().all() else datetime.now().date()
        end_date = st.date_input("End Date", max_date, key="player_ind_end")

    # Apply filters
    filtered_df = df[df['batsman'] == selected_player].copy()

    if selected_team != 'All':
        filtered_df = filtered_df[filtered_df['team'] == selected_team]

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
            stats = calculate_player_stats(filtered_df, phase_key, pi_range)
            if stats['balls_faced'] > 0:  # Only include ranges with data
                stats_data.append({
                    'PI Range': pi_range[2],
                    'Balls Faced': stats['balls_faced'],
                    'Runs': stats['runs_scored'],
                    'Dismissals': stats['wickets'],
                    'Matches': stats['matches'],
                    'Wins': stats['wins'],
                    'Win %': stats['match_win_rate'],
                    'Strike Rate': stats['strike_rate'],
                    'Boundary %': stats['boundary_rate'],
                    'Dot Ball %': stats['dot_ball_rate'],
                    'Success Rate': stats['success_rate'],
                    'Avg PI': stats['avg_pi']
                })

        if stats_data:
            stats_df = pd.DataFrame(stats_data)

            # Style the dataframe
            styled_df = stats_df.style.background_gradient(
                subset=['Success Rate'],
                cmap='RdYlGn',
                vmin=0,
                vmax=100
            ).background_gradient(
                subset=['Win %'],
                cmap='RdYlGn',
                vmin=0,
                vmax=100
            ).background_gradient(
                subset=['Strike Rate'],
                cmap='Blues',
                vmin=0,
                vmax=200
            ).format({
                'Win %': '{:.2f}',
                'Strike Rate': '{:.2f}',
                'Boundary %': '{:.2f}',
                'Dot Ball %': '{:.2f}',
                'Success Rate': '{:.2f}',
                'Avg PI': '{:.2f}'
            })

            st.dataframe(styled_df, use_container_width=True, height=400)

            # Visualization
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Success Rate by PI Range', 'Strike Rate by PI Range'),
                specs=[[{"type": "bar"}, {"type": "bar"}]]
            )

            fig.add_trace(
                go.Bar(
                    x=stats_df['PI Range'],
                    y=stats_df['Success Rate'],
                    name='Success Rate',
                    marker_color=COLORS['target_zone'],
                    text=stats_df['Success Rate'],
                    texttemplate='%{text:.1f}%',
                    textposition='outside'
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Bar(
                    x=stats_df['PI Range'],
                    y=stats_df['Strike Rate'],
                    name='Strike Rate',
                    marker_color=COLORS['pressure_line'],
                    text=stats_df['Strike Rate'],
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


def render_player_comparison(df: pd.DataFrame):
    """Render player comparison section"""

    st.markdown("### Player Comparison")

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Select Players to Compare (2-4 players)**")
        players = sorted(df['batsman'].dropna().unique())
        selected_players = st.multiselect(
            "Players",
            players,
            max_selections=4,
            key="player_comp_players"
        )

    with col2:
        # Phase selection
        phase_options = {v[2]: k for k, v in PHASES.items()}
        selected_phase_name = st.selectbox(
            "Select Phase",
            list(phase_options.keys()),
            key="player_comp_phase"
        )
        selected_phase = phase_options[selected_phase_name]

    if len(selected_players) < 2:
        st.info("Please select at least 2 players to compare")
        return

    # Additional filters
    col1, col2, col3 = st.columns(3)

    with col1:
        oppositions = ['All'] + sorted(df['opposition'].dropna().unique().tolist())
        selected_opposition = st.selectbox("Opposition", oppositions, key="player_comp_opp")

    with col2:
        venues = ['All'] + sorted(df['venue'].dropna().unique().tolist())
        selected_venue = st.selectbox("Venue", venues, key="player_comp_venue")

    with col3:
        # Date range
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        min_date = df['date'].min().date() if not df['date'].isna().all() else datetime.now().date() - timedelta(days=365)
        max_date = df['date'].max().date() if not df['date'].isna().all() else datetime.now().date()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", min_date, key="player_comp_start")
    with col2:
        end_date = st.date_input("End Date", max_date, key="player_comp_end")

    st.markdown("---")

    # Prepare comparison data
    comparison_data = []

    for player in selected_players:
        # Filter data
        player_df = df[df['batsman'] == player].copy()

        if selected_opposition != 'All':
            player_df = player_df[player_df['opposition'] == selected_opposition]

        if selected_venue != 'All':
            player_df = player_df[player_df['venue'] == selected_venue]

        player_df = player_df[
            (player_df['date'] >= pd.to_datetime(start_date)) &
            (player_df['date'] <= pd.to_datetime(end_date))
        ]

        # Calculate stats for each PI range
        for pi_range in PI_RANGES:
            stats = calculate_player_stats(player_df, selected_phase, pi_range)
            if stats['balls_faced'] > 0:
                comparison_data.append({
                    'Player': player,
                    'PI Range': pi_range[2],
                    'Balls': stats['balls_faced'],
                    'Runs': stats['runs_scored'],
                    'Outs': stats['wickets'],
                    'Matches': stats['matches'],
                    'Wins': stats['wins'],
                    'Win %': stats['match_win_rate'],
                    'SR': stats['strike_rate'],
                    'Boundary %': stats['boundary_rate'],
                    'Success Rate': stats['success_rate']
                })

    if not comparison_data:
        st.warning("No data available for selected filters")
        return

    comp_df = pd.DataFrame(comparison_data)

    # Display comparison table
    st.markdown(f"#### Comparison for {selected_phase_name}")

    # Pivot for better visualization
    pivot_df = comp_df.pivot(index='PI Range', columns='Player', values='Success Rate')

    styled_pivot = pivot_df.style.background_gradient(
        cmap='RdYlGn',
        axis=None,
        vmin=0,
        vmax=100
    ).format('{:.2f}')

    st.markdown("**Success Rate Comparison**")
    st.dataframe(styled_pivot, use_container_width=True)

    # Visualization - Success Rate Comparison
    fig = go.Figure()

    colors = [COLORS['pressure_line'], COLORS['target_zone'], COLORS['acceptable_zone'], COLORS['risky_zone']]

    for idx, player in enumerate(selected_players):
        player_data = comp_df[comp_df['Player'] == player]
        fig.add_trace(go.Bar(
            x=player_data['PI Range'],
            y=player_data['Success Rate'],
            name=player,
            marker_color=colors[idx % len(colors)],
            text=player_data['Success Rate'],
            texttemplate='%{text:.1f}',
            textposition='outside'
        ))

    fig.update_layout(
        title=f"Success Rate Comparison - {selected_phase_name}",
        xaxis_title="Pressure Index Range",
        yaxis_title="Success Rate (%)",
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

    # Strike Rate Comparison
    st.markdown("---")
    st.markdown("**Strike Rate Comparison**")

    pivot_sr = comp_df.pivot(index='PI Range', columns='Player', values='SR')
    styled_sr = pivot_sr.style.background_gradient(
        cmap='Blues',
        axis=None,
        vmin=0,
        vmax=200
    ).format('{:.2f}')

    st.dataframe(styled_sr, use_container_width=True)

    # Detailed comparison table
    st.markdown("---")
    st.markdown("**Detailed Statistics**")

    # Format and display full comparison
    display_df = comp_df.copy()
    styled_comp = display_df.style.background_gradient(
        subset=['Success Rate'],
        cmap='RdYlGn',
        vmin=0,
        vmax=100
    ).background_gradient(
        subset=['SR'],
        cmap='Blues',
        vmin=0,
        vmax=200
    ).format({
        'SR': '{:.2f}',
        'Boundary %': '{:.2f}',
        'Success Rate': '{:.2f}'
    })

    st.dataframe(styled_comp, use_container_width=True, height=500)


if __name__ == "__main__":
    render_clutch_players()
