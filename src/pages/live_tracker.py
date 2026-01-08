"""
Live PI Tracker Page
Real-time pressure index tracking for live T20 matches
"""

import streamlit as st
import time
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.pressure_index import (
    PressureIndexCalculator, 
    DuckworthLewisTable,
    get_phase,
    get_phase_display_name,
    get_zone_for_pi,
    calculate_strategic_projections
)
from src.utils.cricinfo_scraper import get_scraper
from src.utils.visualizations import create_pressure_curve, COLORS
from src.components.ui_components import (
    render_match_header,
    render_stats_row,
    render_pi_display,
    render_projections_section,
    render_strategy_tip,
    render_no_data_message,
    render_loading_message
)


def get_dl_table():
    """Get Duckworth-Lewis table"""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(base_path, 'data', 'duckworth_lewis_table.csv')
    return DuckworthLewisTable(csv_path)


def render_live_tracker():
    """Render the Live PI Tracker page"""

    # Try to fetch live matches
    scraper = get_scraper()

    with st.spinner("Fetching live T20 matches..."):
        try:
            live_matches = scraper.get_live_matches()
            t20_live = [m for m in live_matches if m.get('is_live', False)]
        except Exception as e:
            st.error(f"Error fetching live matches: {str(e)}")
            t20_live = []

    if not t20_live:
        # No live matches
        st.info("Unable to track any live men's T20 match at the moment.")
        st.markdown("---")
        st.markdown("""
        **Note:** The Pressure Index can only be calculated during the 2nd innings (run chase) of T20 matches.

        Please check back when a men's T20 match is in progress. The app automatically fetches live match data
        from multiple sources including **ESPN Cricinfo** and **Cricbuzz** to provide comprehensive coverage of
        international matches and domestic leagues (IPL, BBL, BPL, PSL, CPL, SA20, etc.).
        """)
        return

    # Show live matches
    st.markdown("### Live T20 Matches")

    # Create match options with source indicator
    match_options = {}
    match_data = {}  # Store full match data for later use

    for m in t20_live:
        source = m.get('source', 'unknown').upper()
        source_badge = f"[{source}]" if source else ""
        match_label = f"{source_badge} {m.get('name', 'Unknown Match')} - {m.get('status', 'Live')}"
        match_options[match_label] = m['match_id']
        match_data[m['match_id']] = m

    selected_match = st.selectbox(
        "Select a match to view Pressure Index",
        options=list(match_options.keys()),
        key="live_match_select"
    )

    if selected_match:
        match_id = match_options[selected_match]

        # Auto-refresh option
        col1, col2 = st.columns([4, 1])
        with col1:
            auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=False, key="auto_refresh")
        with col2:
            if st.button("Refresh", key="manual_refresh", use_container_width=True):
                # Clear cache for this match
                scraper.cache.pop(f'match_{match_id}', None)
                scraper.cache.pop('live_matches', None)
                st.rerun()

        # Render match details first
        render_match_details(match_id, scraper)

        # Auto-refresh at the end
        if auto_refresh:
            # Clear cache before refresh to ensure fresh data
            time.sleep(30)
            scraper.cache.pop(f'match_{match_id}', None)
            scraper.cache.pop('live_matches', None)
            st.rerun()


def render_match_details(match_id: str, scraper):
    """Render detailed match view with PI calculations"""
    
    with st.spinner("Loading match details..."):
        try:
            score_data = scraper.get_live_score_data(match_id)
        except Exception as e:
            st.error(f"Error loading match: {str(e)}")
            return
    
    if not score_data:
        render_no_data_message("Unable to load match details. Please try again.")
        return
    
    # Check if second innings
    if not score_data.get('is_second_innings', False):
        st.warning("Pressure Index is only calculated during the 2nd innings (run chase). "
                  "This match is currently in the 1st innings.")
        
        # Show basic match info
        render_match_header(
            team1=score_data.get('batting_team', 'Team 1'),
            team2=score_data.get('bowling_team', 'Team 2'),
            venue=score_data.get('venue', ''),
            competition=score_data.get('series', '')
        )
        
        st.markdown(f"**Current Score:** {score_data.get('runs_scored', 0)}/{score_data.get('wickets_lost', 0)} "
                   f"({score_data.get('overs', 0)} overs)")
        return
    
    # Load DL table and calculate PI
    try:
        dl_table = get_dl_table()
        pi_calc = PressureIndexCalculator(dl_table)
    except Exception as e:
        st.error(f"Error initializing calculations: {str(e)}")
        return
    
    target = score_data.get('target', 0)
    runs = score_data.get('runs_scored', 0)
    wickets = score_data.get('wickets_lost', 0)
    balls = score_data.get('balls_faced', 0)
    overs = score_data.get('overs', 0)
    
    # Calculate PI
    current_pi = pi_calc.calculate_pressure_index(
        target=target,
        runs_scored=runs,
        balls_faced=balls,
        wickets_lost=wickets
    )
    
    # Get phase and zone
    current_over = balls // 6 + 1
    phase = get_phase(current_over)
    phase_display = get_phase_display_name(phase)
    zone = get_zone_for_pi(current_pi, phase)
    
    # Calculate additional stats
    runs_needed = target - runs
    balls_remaining = 120 - balls
    required_rr = (runs_needed * 6) / balls_remaining if balls_remaining > 0 else 0
    
    # Render match header
    st.markdown("---")
    render_match_header(
        team1=score_data.get('batting_team', 'Batting Team'),
        team2=score_data.get('bowling_team', 'Bowling Team'),
        target=target,
        venue=score_data.get('venue', ''),
        competition=score_data.get('series', '')
    )
    
    # Stats row
    stats = [
        {
            'label': 'Score',
            'value': f"{runs}/{wickets}",
            'sublabel': f"{overs} overs"
        },
        {
            'label': 'Runs Needed',
            'value': str(runs_needed),
            'sublabel': f"from {balls_remaining} balls"
        },
        {
            'label': 'Phase',
            'value': phase_display,
            'sublabel': f"Over {current_over}"
        },
        {
            'label': 'Pressure Index',
            'value': f"{current_pi:.2f}",
            'sublabel': zone.replace('_', ' ').title(),
            'color_class': f"pi-{zone}" if zone != 'avoid' else 'pi-high'
        }
    ]
    
    render_stats_row(stats)
    
    # Current batsmen and bowler info
    batsmen = score_data.get('batsmen', [])
    bowlers = score_data.get('bowlers', [])
    
    if batsmen or bowlers:
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**At the Crease:**")
            for bat in batsmen:
                strike = "•" if bat.get('on_strike', False) else ""
                st.markdown(f"- {bat.get('name', 'Unknown')}: {bat.get('runs', 0)}({bat.get('balls', 0)}) {strike}")
        
        with col2:
            st.markdown("**Bowling:**")
            for bowl in bowlers:
                st.markdown(f"- {bowl.get('name', 'Unknown')}: {bowl.get('wickets', 0)}/{bowl.get('runs', 0)} ({bowl.get('overs', 0)} ov)")
    
    # Strategic projections
    st.markdown("---")
    projections = calculate_strategic_projections(
        target=target,
        runs_scored=runs,
        balls_faced=balls,
        wickets_lost=wickets,
        dl_table=dl_table
    )
    
    render_projections_section(projections)
    
    # Pressure Curve - Try to get ball-by-ball data first
    st.markdown("---")
    st.markdown("### Pressure Curve")

    # Try to fetch ball-by-ball data from ESPN
    with st.spinner("Fetching ball-by-ball commentary data..."):
        ball_by_ball = scraper.get_ball_by_ball_data(match_id)

    pi_data = []
    using_actual_data = False

    if ball_by_ball and len(ball_by_ball) > 0:
        using_actual_data = True

        # We have actual ball-by-ball data from ESPN commentary
        # Calculate PI for each ball
        for idx, ball_info in enumerate(ball_by_ball):
            ball_num = idx + 1
            ball_runs = ball_info.get('runs', 0)
            ball_wickets = ball_info.get('wickets', 0)

            try:
                ball_pi = pi_calc.calculate_pressure_index(
                    target=target,
                    runs_scored=ball_runs,
                    balls_faced=ball_num,
                    wickets_lost=ball_wickets
                )

                pi_data.append({
                    'ball': ball_num,
                    'over': (ball_num - 1) // 6 + 1,
                    'pressure_index': ball_pi,
                    'runs': ball_runs,
                    'wickets': ball_wickets,
                    'is_wicket': ball_info.get('is_wicket', False),
                    'runs_scored': ball_info.get('runs_scored', 0)
                })
            except Exception:
                continue
    else:
        # Fallback: Generate realistic estimated pressure curve based on current match state
        # Since we don't have ball-by-ball data, estimate based on typical T20 progression
        st.info("ℹ️ Ball-by-ball commentary not available from ESPN. Using estimated progression based on current match state.")

        import math

        # Calculate overall run rate achieved so far
        overall_rr = (runs / balls * 6) if balls > 0 else 0

        # Generate realistic run and wicket progression
        for ball_num in range(1, balls + 1):
            over_num = (ball_num - 1) // 6 + 1
            progress = ball_num / balls

            # Estimate runs with realistic T20 pattern
            # T20 chases typically follow: steady start, consolidation, acceleration
            # Use a polynomial progression that matches current state

            # Create a curve that:
            # - Starts slower (cautious start)
            # - Accelerates in middle if needed
            # - Must reach actual score at current ball

            # Use a quadratic progression adjusted to match current score
            # progress^1.2 creates slight acceleration over time
            estimated_runs = int((progress ** 1.2) * runs)

            # Smooth out any jumps and ensure monotonic increase
            if ball_num > 1 and estimated_runs < pi_data[-1]['runs']:
                estimated_runs = pi_data[-1]['runs']

            # Ensure we reach exact current score at current ball
            if ball_num == balls:
                estimated_runs = runs

            # Estimate wickets with realistic T20 pattern
            if wickets > 0:
                # Wickets typically fall gradually with some clustering
                # Use exponential distribution (more wickets as innings progresses)
                wicket_progress = progress ** 1.5
                estimated_wickets = int(wicket_progress * wickets)

                # Ensure monotonic increase
                if ball_num > 1 and estimated_wickets < pi_data[-1]['wickets']:
                    estimated_wickets = pi_data[-1]['wickets']

                # Ensure we reach exact wickets at current ball
                if ball_num == balls:
                    estimated_wickets = wickets
            else:
                estimated_wickets = 0

            # Calculate PI for this estimated state
            try:
                ball_pi = pi_calc.calculate_pressure_index(
                    target=target,
                    runs_scored=estimated_runs,
                    balls_faced=ball_num,
                    wickets_lost=estimated_wickets
                )

                pi_data.append({
                    'ball': ball_num,
                    'over': (ball_num - 1) // 6 + 1,
                    'pressure_index': ball_pi,
                    'runs': estimated_runs,
                    'wickets': estimated_wickets,
                    'is_wicket': False,
                    'runs_scored': 0
                })
            except Exception:
                continue

    if pi_data:
        from src.utils.visualizations import create_pressure_curve

        fig = create_pressure_curve(
            pi_data=pi_data,
            title=f"Pressure Index Progression - {score_data.get('batting_team', '')} Chase",
            show_wickets=True,
            show_phase_markers=True,
            height=450,
            use_dynamic_zones=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # Show summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_pi = sum(d['pressure_index'] for d in pi_data) / len(pi_data)
            st.metric("Average PI", f"{avg_pi:.2f}")
        with col2:
            max_pi_val = max(d['pressure_index'] for d in pi_data)
            st.metric("Peak PI", f"{max_pi_val:.2f}")
        with col3:
            st.metric("Current Ball", f"{balls}/120")

        # Show data source info only for estimated data
        if not using_actual_data:
            st.caption("ℹ️ Ball-by-ball data unavailable. Curve shows estimated progression based on current match state (Target: {}, Score: {}/{}, Balls: {}/120). "
                      "Pressure Index is calculated accurately for the current state.".format(target, runs, wickets, balls))

    # Strategy tip
    st.markdown("---")
    st.markdown("### Strategy Recommendation")

    if current_pi < 0.5:
        tip = "Excellent position! Maintain current scoring rate to ensure victory."
    elif current_pi < 1.5:
        tip = "Good control. Score the required runs shown above to move into the Target Zone."
    elif current_pi < 2.5:
        tip = "Under pressure. Focus on building partnerships while maintaining the required rate."
    else:
        tip = "High pressure situation. Need to accelerate immediately while protecting wickets."
    
    render_strategy_tip(tip)


if __name__ == "__main__":
    render_live_tracker()
