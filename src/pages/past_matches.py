"""
Past Matches Page
Historical match analysis and comparisons
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.pressure_index import (
    PressureIndexCalculator,
    DuckworthLewisTable,
    get_phase,
    get_phase_display_name
)
from src.utils.data_handler import MatchDataHandler
from src.utils.csv_loader import load_csv_data
from src.utils.visualizations import (
    create_pressure_curve,
    create_comparison_curve,
    create_live_comparison_curve,
    create_over_summary_chart,
    create_empty_chart,
    COLORS
)
from src.utils.cricinfo_scraper import get_scraper
from src.components.ui_components import (
    render_match_header,
    render_stats_row,
    render_footer,
    render_no_data_message
)


def get_dl_table():
    """Get Duckworth-Lewis table"""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(base_path, 'data', 'duckworth_lewis_table.csv')
    return DuckworthLewisTable(csv_path)


@st.cache_resource
def get_data_handler():
    """Get data handler for historical matches from Dropbox"""
    try:
        df = load_csv_data()
        return MatchDataHandler(df=df)
    except Exception as e:
        st.error(f"Error loading data from Dropbox: {str(e)}")
        return None


def render_past_matches():
    """Render the Past Matches page"""

    # Check if data is available
    with st.spinner("Loading historical match data from Dropbox..."):
        data_handler = get_data_handler()

    if data_handler is None or data_handler.df.empty:
        st.error("Unable to load historical match data from Dropbox. Please check your internet connection.")
        return
    
    # Create tabs for different features
    tab1, tab2, tab3 = st.tabs([
        "Historical Match Data",
        "Compare Past Matches", 
        "Compare with Live Match"
    ])
    
    with tab1:
        render_historical_data(data_handler)
    
    with tab2:
        render_match_comparison(data_handler)
    
    with tab3:
        render_live_comparison(data_handler)


def render_historical_data(data_handler: MatchDataHandler):
    """Render historical match data section"""
    
    st.markdown("### Historical Match Data")
    st.markdown("Search and view detailed pressure analysis for past matches")
    
    # Get filter options
    batting_teams, bowling_teams = data_handler.get_unique_teams()
    min_date, max_date = data_handler.get_date_range()
    competitions = data_handler.get_unique_competitions()
    
    # Filters
    st.markdown("#### Search Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=min_date if min_date else datetime(2019, 1, 1),
            min_value=min_date,
            max_value=max_date,
            key="hist_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=max_date if max_date else datetime.now(),
            min_value=min_date,
            max_value=max_date,
            key="hist_end_date"
        )
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        chasing_team = st.selectbox(
            "Chasing Team",
            options=['All'] + batting_teams,
            key="hist_chasing"
        )
    
    with col4:
        bowling_team = st.selectbox(
            "Bowling Team",
            options=['All'] + bowling_teams,
            key="hist_bowling"
        )
    
    with col5:
        competition = st.selectbox(
            "Competition",
            options=['All'] + competitions,
            key="hist_competition"
        )
    
    # Search button
    hist_search_clicked = st.button("Search Matches", key="search_hist_btn")

    if hist_search_clicked:
        # Search matches and store in session state
        matches = data_handler.search_matches(
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time()),
            batting_team=chasing_team if chasing_team != 'All' else None,
            bowling_team=bowling_team if bowling_team != 'All' else None,
            competition=competition if competition != 'All' else None
        )

        if not matches:
            render_no_data_message("No matches found with the selected filters.")
            st.session_state.pop('hist_matches', None)
            return

        # Store in session state
        st.session_state['hist_matches'] = matches

    # Display results if we have them
    if 'hist_matches' in st.session_state:
        matches = st.session_state['hist_matches']

        st.markdown(f"**Found {len(matches)} matches**")

        # Create match selection
        match_options = {
            f"{m['date'].strftime('%Y-%m-%d') if isinstance(m['date'], datetime) else m['date']} - "
            f"{m['batting_team']} vs {m['bowling_team']} ({m['result']})": m['match_id']
            for m in matches[:100]  # Limit to 100 matches
        }

        selected_match = st.selectbox(
            "Select a match to view details",
            options=list(match_options.keys()),
            key="hist_match_select"
        )

        if selected_match:
            match_id = match_options[selected_match]
            render_match_details(data_handler, match_id)


def render_match_details(data_handler: MatchDataHandler, match_id: int):
    """Render detailed view of a specific match"""
    
    # Get match summary
    summary = data_handler.get_match_summary(match_id)
    
    if not summary:
        render_no_data_message("Unable to load match details.")
        return
    
    st.markdown("---")
    
    # Match header
    render_match_header(
        team1=summary['batting_team'],
        team2=summary['bowling_team'],
        target=summary['target'],
        venue=summary['ground'],
        competition=summary['competition']
    )
    
    # Match summary stats
    date_str = summary['date'].strftime('%B %d, %Y') if isinstance(summary['date'], datetime) else str(summary['date'])
    
    stats = [
        {'label': 'Date', 'value': date_str},
        {'label': 'Final Score', 'value': f"{summary['final_score']}/{summary['final_wickets']}"},
        {'label': 'Target', 'value': str(summary['target'])},
        {
            'label': 'Result',
            'value': summary['result'],
            'color_class': 'pi-target' if summary['result'] == 'Won' else 'pi-risky'
        }
    ]
    
    render_stats_row(stats)
    
    # Calculate PI for match
    try:
        dl_table = get_dl_table()
        pi_calc = PressureIndexCalculator(dl_table)
        
        pi_data = data_handler.calculate_pi_for_match(match_id, pi_calc)
        
        if pi_data:
            # Pressure Curve
            st.markdown("---")
            st.markdown("### Pressure Curve")
            
            fig = create_pressure_curve(
                pi_data=pi_data,
                title=f"{summary['batting_team']} chasing {summary['target']}",
                show_zones=True,
                show_wickets=True,
                show_phase_markers=True,
                height=450
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Over-by-over summary
            st.markdown("---")
            st.markdown("### Over-by-Over Summary")
            
            over_data = data_handler.get_over_summary(match_id)
            
            if over_data:
                fig_overs = create_over_summary_chart(
                    over_data=over_data,
                    title="Runs and Wickets per Over",
                    height=300
                )
                
                st.plotly_chart(fig_overs, use_container_width=True)

            # Key moments and insights
            st.markdown("---")
            st.markdown("### Match Insights")

            # Find max/min PI
            max_pi = max(pi_data, key=lambda x: x['pressure_index'])
            min_pi = min(pi_data, key=lambda x: x['pressure_index'] if x['pressure_index'] > 0 else float('inf'))

            # Pressure extremes cards
            col1, col2 = st.columns(2)

            with col1:
                max_over = (max_pi['ball'] - 1) // 6 + 1
                max_ball_in_over = (max_pi['ball'] - 1) % 6 + 1
                st.markdown(f"""
                <div class="card" style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.1) 100%); border-left: 4px solid #ef4444;">
                    <div style="color: #94a3b8; font-size: 12px; text-transform: uppercase; margin-bottom: 8px;">Highest Pressure</div>
                    <div style="color: #ef4444; font-size: 32px; font-weight: 700; margin-bottom: 4px;">{max_pi['pressure_index']:.2f}</div>
                    <div style="color: #e2e8f0; font-size: 14px;">Over {max_over}.{max_ball_in_over}</div>
                    <div style="color: #94a3b8; font-size: 13px; margin-top: 4px;">Score: {max_pi.get('runs', 'N/A')}/{max_pi.get('wickets', 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                min_over = (min_pi['ball'] - 1) // 6 + 1
                min_ball_in_over = (min_pi['ball'] - 1) % 6 + 1
                st.markdown(f"""
                <div class="card" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.1) 100%); border-left: 4px solid #10b981;">
                    <div style="color: #94a3b8; font-size: 12px; text-transform: uppercase; margin-bottom: 8px;">Lowest Pressure</div>
                    <div style="color: #10b981; font-size: 32px; font-weight: 700; margin-bottom: 4px;">{min_pi['pressure_index']:.2f}</div>
                    <div style="color: #e2e8f0; font-size: 14px;">Over {min_over}.{min_ball_in_over}</div>
                    <div style="color: #94a3b8; font-size: 13px; margin-top: 4px;">Score: {min_pi.get('runs', 'N/A')}/{min_pi.get('wickets', 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)

            # Detect pressure turning points (significant changes)
            st.markdown("#### Pressure Turning Points")

            turning_points = []
            for i in range(1, len(pi_data) - 1):
                prev_pi = pi_data[i-1]['pressure_index']
                curr_pi = pi_data[i]['pressure_index']
                next_pi = pi_data[i+1]['pressure_index']

                # Detect significant change (increase or decrease)
                change_from_prev = curr_pi - prev_pi
                change_to_next = next_pi - curr_pi

                # If change direction reverses and magnitude is significant
                if abs(change_from_prev) > 0.3 or abs(change_to_next) > 0.3:
                    if (change_from_prev > 0 and change_to_next < 0) or (change_from_prev < 0 and change_to_next > 0):
                        turning_points.append({
                            'ball': pi_data[i]['ball'],
                            'over': pi_data[i]['over'],
                            'pi': curr_pi,
                            'change': change_from_prev,
                            'runs': pi_data[i].get('runs', 'N/A'),
                            'wickets': pi_data[i].get('wickets', 'N/A'),
                            'is_wicket': pi_data[i].get('is_wicket', False)
                        })

            # Also add wicket moments
            wicket_moments = [d for d in pi_data if d.get('is_wicket', False)]

            # Combine and deduplicate
            all_moments = []
            for wp in wicket_moments:
                all_moments.append({
                    'ball': wp['ball'],
                    'over': wp['over'],
                    'pi': wp['pressure_index'],
                    'runs': wp.get('runs', 'N/A'),
                    'wickets': wp.get('wickets', 'N/A'),
                    'type': 'Wicket',
                    'is_wicket': True,
                    'batsman': wp.get('batsman', ''),
                    'bowler': wp.get('bowler', '')
                })

            for tp in turning_points:
                if not any(m['ball'] == tp['ball'] and m.get('is_wicket') for m in all_moments):
                    change_type = 'Pressure Spike' if tp['change'] > 0 else 'Pressure Relief'
                    # Find the corresponding data point to get batsman and bowler
                    tp_data = next((d for d in pi_data if d['ball'] == tp['ball']), {})
                    all_moments.append({
                        'ball': tp['ball'],
                        'over': tp['over'],
                        'pi': tp['pi'],
                        'runs': tp['runs'],
                        'wickets': tp['wickets'],
                        'type': change_type,
                        'is_wicket': False,
                        'batsman': tp_data.get('batsman', ''),
                        'bowler': tp_data.get('bowler', '')
                    })

            # Sort by ball
            all_moments = sorted(all_moments, key=lambda x: x['ball'])

            # Display turning points in a grid
            if all_moments:
                # Limit to most significant moments (max 8)
                all_moments = all_moments[:8]

                cols_per_row = 2
                for i in range(0, len(all_moments), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        if i + j < len(all_moments):
                            moment = all_moments[i + j]
                            ball_in_over = (moment['ball'] - 1) % 6 + 1

                            # Color based on type
                            if moment['type'] == 'Wicket':
                                border_color = '#ef4444'
                                bg_gradient = 'rgba(239, 68, 68, 0.1)'
                            elif moment['type'] == 'Pressure Spike':
                                border_color = '#f59e0b'
                                bg_gradient = 'rgba(245, 158, 11, 0.1)'
                            else:
                                border_color = '#10b981'
                                bg_gradient = 'rgba(16, 185, 129, 0.1)'

                            with col:
                                # Build player info
                                batsman = moment.get('batsman', '')
                                bowler = moment.get('bowler', '')

                                player_info = ""
                                if batsman and batsman != 'N/A' and str(batsman) != 'nan':
                                    player_info += f'<div style="color: #64748b; font-size: 11px; margin-top: 4px;">Bat: {batsman}</div>'
                                if bowler and bowler != 'N/A' and str(bowler) != 'nan':
                                    player_info += f'<div style="color: #64748b; font-size: 11px;">Bowl: {bowler}</div>'

                                st.markdown(f"""
                                <div class="card" style="background: {bg_gradient}; border-left: 3px solid {border_color}; padding: 14px;">
                                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                                        <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase;">{moment['type']}</div>
                                        <div style="color: #e2e8f0; font-size: 13px; font-weight: 600;">Over {moment['over']}.{ball_in_over}</div>
                                    </div>
                                    <div style="color: #e2e8f0; font-size: 18px; font-weight: 600; margin-bottom: 6px;">PI: {moment['pi']:.2f}</div>
                                    <div style="color: #94a3b8; font-size: 12px;">Score: {moment['runs']}/{moment['wickets']}</div>
                                    {player_info}
                                </div>
                                """, unsafe_allow_html=True)
            else:
                st.info("No significant turning points detected in this chase.")
        
    except Exception as e:
        st.error(f"Error calculating pressure index: {str(e)}")


def render_match_comparison(data_handler: MatchDataHandler):
    """Render match comparison section"""
    
    st.markdown("### Compare Past Matches")
    st.markdown("Compare pressure curves of two different run chases")
    
    # Get filter options
    batting_teams, bowling_teams = data_handler.get_unique_teams()
    min_date, max_date = data_handler.get_date_range()
    
    # Match 1 filters
    st.markdown("#### Match 1")
    
    col1, col2 = st.columns(2)
    
    with col1:
        m1_start = st.date_input(
            "Start Date",
            value=min_date,
            key="m1_start"
        )
        m1_batting = st.selectbox(
            "Chasing Team",
            options=['All'] + batting_teams,
            key="m1_batting"
        )
    
    with col2:
        m1_end = st.date_input(
            "End Date",
            value=max_date,
            key="m1_end"
        )
        m1_bowling = st.selectbox(
            "Bowling Team",
            options=['All'] + bowling_teams,
            key="m1_bowling"
        )
    
    # Match 2 filters
    st.markdown("#### Match 2")
    
    col3, col4 = st.columns(2)
    
    with col3:
        m2_start = st.date_input(
            "Start Date",
            value=min_date,
            key="m2_start"
        )
        m2_batting = st.selectbox(
            "Chasing Team",
            options=['All'] + batting_teams,
            key="m2_batting"
        )
    
    with col4:
        m2_end = st.date_input(
            "End Date",
            value=max_date,
            key="m2_end"
        )
        m2_bowling = st.selectbox(
            "Bowling Team",
            options=['All'] + bowling_teams,
            key="m2_bowling"
        )
    
    compare_search_clicked = st.button("Find Matches to Compare", key="compare_search_btn")

    if compare_search_clicked:
        # Search for both matches and store in session state
        matches_1 = data_handler.search_matches(
            start_date=datetime.combine(m1_start, datetime.min.time()),
            end_date=datetime.combine(m1_end, datetime.max.time()),
            batting_team=m1_batting if m1_batting != 'All' else None,
            bowling_team=m1_bowling if m1_bowling != 'All' else None
        )

        matches_2 = data_handler.search_matches(
            start_date=datetime.combine(m2_start, datetime.min.time()),
            end_date=datetime.combine(m2_end, datetime.max.time()),
            batting_team=m2_batting if m2_batting != 'All' else None,
            bowling_team=m2_bowling if m2_bowling != 'All' else None
        )

        if not matches_1 or not matches_2:
            render_no_data_message("No matches found for one or both selections.")
            return

        # Store in session state
        st.session_state['compare_matches_1'] = matches_1
        st.session_state['compare_matches_2'] = matches_2

    # Display match selection if we have results
    if 'compare_matches_1' in st.session_state and 'compare_matches_2' in st.session_state:
        matches_1 = st.session_state['compare_matches_1']
        matches_2 = st.session_state['compare_matches_2']

        col1, col2 = st.columns(2)

        with col1:
            match_1_options = {
                f"{m['date'].strftime('%Y-%m-%d') if isinstance(m['date'], datetime) else m['date']} - "
                f"{m['batting_team']} vs {m['bowling_team']}": m['match_id']
                for m in matches_1[:50]
            }
            selected_1 = st.selectbox(
                "Select Match 1",
                options=list(match_1_options.keys()),
                key="compare_m1"
            )

        with col2:
            match_2_options = {
                f"{m['date'].strftime('%Y-%m-%d') if isinstance(m['date'], datetime) else m['date']} - "
                f"{m['batting_team']} vs {m['bowling_team']}": m['match_id']
                for m in matches_2[:50]
            }
            selected_2 = st.selectbox(
                "Select Match 2",
                options=list(match_2_options.keys()),
                key="compare_m2"
            )

        do_compare_clicked = st.button("Compare Matches", key="do_compare_btn")

        if do_compare_clicked and selected_1 and selected_2:
            match_id_1 = match_1_options[selected_1]
            match_id_2 = match_2_options[selected_2]
            
            # Get summaries
            summary_1 = data_handler.get_match_summary(match_id_1)
            summary_2 = data_handler.get_match_summary(match_id_2)
            
            if not summary_1 or not summary_2:
                st.error("Unable to load match data.")
                return
            
            # Calculate PI for both matches
            try:
                dl_table = get_dl_table()
                pi_calc = PressureIndexCalculator(dl_table)
                
                pi_data_1 = data_handler.calculate_pi_for_match(match_id_1, pi_calc)
                pi_data_2 = data_handler.calculate_pi_for_match(match_id_2, pi_calc)
                
                if pi_data_1 and pi_data_2:
                    # Create comparison chart
                    st.markdown("---")
                    st.markdown("### Pressure Curve Comparison")
                    
                    label_1 = f"{summary_1['batting_team']} vs {summary_1['bowling_team']}"
                    label_2 = f"{summary_2['batting_team']} vs {summary_2['bowling_team']}"
                    
                    fig = create_comparison_curve(
                        pi_data_1=pi_data_1,
                        pi_data_2=pi_data_2,
                        label_1=label_1,
                        label_2=label_2,
                        title="Pressure Curve Comparison",
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

                    # Comparative insights
                    st.markdown("---")
                    st.markdown("### Comparative Insights")

                    # Match summaries in cards
                    col1, col2 = st.columns(2)

                    max_pi_1 = max(d['pressure_index'] for d in pi_data_1)
                    avg_pi_1 = sum(d['pressure_index'] for d in pi_data_1) / len(pi_data_1)
                    max_pi_2 = max(d['pressure_index'] for d in pi_data_2)
                    avg_pi_2 = sum(d['pressure_index'] for d in pi_data_2) / len(pi_data_2)

                    with col1:
                        result_color = '#10b981' if summary_1['result'] == 'Won' else '#ef4444'
                        st.markdown(f"""
                        <div class="card" style="border-left: 4px solid {result_color};">
                            <div style="color: #e2e8f0; font-size: 16px; font-weight: 600; margin-bottom: 12px;">{label_1}</div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="color: #94a3b8; font-size: 13px;">Target:</span>
                                <span style="color: #e2e8f0; font-size: 13px; font-weight: 500;">{summary_1['target']}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="color: #94a3b8; font-size: 13px;">Final Score:</span>
                                <span style="color: #e2e8f0; font-size: 13px; font-weight: 500;">{summary_1['final_score']}/{summary_1['final_wickets']}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="color: #94a3b8; font-size: 13px;">Result:</span>
                                <span style="color: {result_color}; font-size: 13px; font-weight: 600;">{summary_1['result']}</span>
                            </div>
                            <div style="border-top: 1px solid #1e3a5f; margin: 10px 0; padding-top: 10px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                    <span style="color: #94a3b8; font-size: 12px;">Max PI:</span>
                                    <span style="color: #ef4444; font-size: 12px; font-weight: 600;">{max_pi_1:.2f}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: #94a3b8; font-size: 12px;">Avg PI:</span>
                                    <span style="color: #f59e0b; font-size: 12px; font-weight: 600;">{avg_pi_1:.2f}</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        result_color = '#10b981' if summary_2['result'] == 'Won' else '#ef4444'
                        st.markdown(f"""
                        <div class="card" style="border-left: 4px solid {result_color};">
                            <div style="color: #e2e8f0; font-size: 16px; font-weight: 600; margin-bottom: 12px;">{label_2}</div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="color: #94a3b8; font-size: 13px;">Target:</span>
                                <span style="color: #e2e8f0; font-size: 13px; font-weight: 500;">{summary_2['target']}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="color: #94a3b8; font-size: 13px;">Final Score:</span>
                                <span style="color: #e2e8f0; font-size: 13px; font-weight: 500;">{summary_2['final_score']}/{summary_2['final_wickets']}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="color: #94a3b8; font-size: 13px;">Result:</span>
                                <span style="color: {result_color}; font-size: 13px; font-weight: 600;">{summary_2['result']}</span>
                            </div>
                            <div style="border-top: 1px solid #1e3a5f; margin: 10px 0; padding-top: 10px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                    <span style="color: #94a3b8; font-size: 12px;">Max PI:</span>
                                    <span style="color: #ef4444; font-size: 12px; font-weight: 600;">{max_pi_2:.2f}</span>
                                </div>
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: #94a3b8; font-size: 12px;">Avg PI:</span>
                                    <span style="color: #f59e0b; font-size: 12px; font-weight: 600;">{avg_pi_2:.2f}</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Key differences
                    st.markdown("#### Key Differences")

                    diff_col1, diff_col2, diff_col3 = st.columns(3)

                    with diff_col1:
                        target_diff = summary_2['target'] - summary_1['target']
                        diff_sign = '+' if target_diff > 0 else ''
                        st.markdown(f"""
                        <div class="card" style="text-align: center; padding: 16px;">
                            <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">Target Difference</div>
                            <div style="color: #e2e8f0; font-size: 24px; font-weight: 700;">{diff_sign}{target_diff}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with diff_col2:
                        max_pi_diff = max_pi_2 - max_pi_1
                        diff_sign = '+' if max_pi_diff > 0 else ''
                        diff_color = '#ef4444' if max_pi_diff > 0 else '#10b981'
                        st.markdown(f"""
                        <div class="card" style="text-align: center; padding: 16px;">
                            <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">Max PI Difference</div>
                            <div style="color: {diff_color}; font-size: 24px; font-weight: 700;">{diff_sign}{max_pi_diff:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with diff_col3:
                        avg_pi_diff = avg_pi_2 - avg_pi_1
                        diff_sign = '+' if avg_pi_diff > 0 else ''
                        diff_color = '#ef4444' if avg_pi_diff > 0 else '#10b981'
                        st.markdown(f"""
                        <div class="card" style="text-align: center; padding: 16px;">
                            <div style="color: #94a3b8; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">Avg PI Difference</div>
                            <div style="color: {diff_color}; font-size: 24px; font-weight: 700;">{diff_sign}{avg_pi_diff:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error comparing matches: {str(e)}")


def render_live_comparison(data_handler: MatchDataHandler):
    """Render live vs past match comparison"""
    
    st.markdown("### Compare with Live Match")
    st.markdown("Compare a live match's pressure progression with a past match")
    
    # Check for live matches
    scraper = get_scraper()
    
    try:
        live_matches = scraper.get_live_matches()
        t20_live = [m for m in live_matches if m.get('is_live', False)]
    except:
        t20_live = []
    
    if not t20_live:
        st.info(
            "No live T20 matches currently in progress. "
            "This feature allows you to compare an ongoing match's pressure curve "
            "with a historical match in real-time."
        )
        return
    
    # Live match selection
    st.markdown("#### Select Live Match")
    
    live_options = {
        f"{m['name']} - {m.get('status', 'Live')}": m['match_id']
        for m in t20_live
    }
    
    selected_live = st.selectbox(
        "Live Match",
        options=list(live_options.keys()),
        key="live_compare"
    )
    
    # Past match selection
    st.markdown("#### Select Past Match to Compare")
    
    batting_teams, bowling_teams = data_handler.get_unique_teams()
    min_date, max_date = data_handler.get_date_range()
    
    col1, col2 = st.columns(2)
    
    with col1:
        past_start = st.date_input("Start Date", value=min_date, key="past_start")
        past_batting = st.selectbox(
            "Chasing Team",
            options=['All'] + batting_teams,
            key="past_batting"
        )
    
    with col2:
        past_end = st.date_input("End Date", value=max_date, key="past_end")
        past_bowling = st.selectbox(
            "Bowling Team",
            options=['All'] + bowling_teams,
            key="past_bowling"
        )
    
    find_past_clicked = st.button("Find Past Matches", key="find_past_btn")

    if find_past_clicked:
        past_matches = data_handler.search_matches(
            start_date=datetime.combine(past_start, datetime.min.time()),
            end_date=datetime.combine(past_end, datetime.max.time()),
            batting_team=past_batting if past_batting != 'All' else None,
            bowling_team=past_bowling if past_bowling != 'All' else None
        )

        if not past_matches:
            render_no_data_message("No past matches found.")
            st.session_state.pop('live_compare_past_matches', None)
            return

        # Store in session state
        st.session_state['live_compare_past_matches'] = past_matches
        st.session_state['live_compare_live_match'] = selected_live

    # Display results if we have them
    if 'live_compare_past_matches' in st.session_state:
        past_matches = st.session_state['live_compare_past_matches']
        selected_live = st.session_state.get('live_compare_live_match', selected_live)

        past_options = {
            f"{m['date'].strftime('%Y-%m-%d') if isinstance(m['date'], datetime) else m['date']} - "
            f"{m['batting_team']} vs {m['bowling_team']}": m['match_id']
            for m in past_matches[:50]
        }

        selected_past = st.selectbox(
            "Select Past Match",
            options=list(past_options.keys()),
            key="past_select"
        )

        do_live_compare_clicked = st.button("Compare", key="do_live_compare_btn")

        if do_live_compare_clicked and selected_live and selected_past:
            live_id = live_options[selected_live]
            past_id = past_options[selected_past]
            
            # Get data
            try:
                dl_table = get_dl_table()
                pi_calc = PressureIndexCalculator(dl_table)
                
                # Past match data
                past_summary = data_handler.get_match_summary(past_id)
                past_pi_data = data_handler.calculate_pi_for_match(past_id, pi_calc)
                
                # Live match data (simplified - would need more robust implementation)
                live_data = scraper.get_live_score_data(live_id)
                
                if past_pi_data and live_data:
                    st.markdown("---")
                    st.markdown("### Live vs Past Comparison")
                    
                    # Build live PI data from current state
                    live_pi_data = []
                    
                    if live_data.get('is_second_innings', False):
                        target = live_data.get('target', 0)
                        runs = live_data.get('runs_scored', 0)
                        wickets = live_data.get('wickets_lost', 0)
                        balls = live_data.get('balls_faced', 0)
                        
                        # Generate approximate PI curve
                        for b in range(1, balls + 1):
                            approx_runs = int((b / balls) * runs) if balls > 0 else 0
                            approx_wickets = int((b / balls) * wickets) if balls > 0 else 0
                            
                            pi = pi_calc.calculate_pressure_index(
                                target=target,
                                runs_scored=approx_runs,
                                balls_faced=b,
                                wickets_lost=approx_wickets
                            )
                            
                            live_pi_data.append({
                                'ball': b,
                                'pressure_index': pi,
                                'is_wicket': False
                            })
                    
                    if live_pi_data:
                        past_label = f"{past_summary['batting_team']} vs {past_summary['bowling_team']}"
                        
                        fig = create_live_comparison_curve(
                            past_pi_data=past_pi_data,
                            live_pi_data=live_pi_data,
                            past_label=past_label,
                            title="Live Match vs Past Match Comparison",
                            height=500
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Live match is not in the second innings yet.")
                
            except Exception as e:
                st.error(f"Error comparing: {str(e)}")


if __name__ == "__main__":
    render_past_matches()
