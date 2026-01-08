"""
Visualization Module
Creates pressure curves and other visualizations using Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import List, Dict, Optional, Tuple


# Color scheme matching the Base44 app
COLORS = {
    'background': '#0a1628',
    'card_bg': '#111c32',
    'text': '#e2e8f0',
    'text_secondary': '#94a3b8',
    'target_zone': '#10b981',  # Green
    'acceptable_zone': '#f59e0b',  # Yellow/Orange
    'risky_zone': '#ef4444',  # Red
    'avoid_zone': '#dc2626',  # Dark red
    'pressure_line': '#3b82f6',  # Blue
    'wicket_marker': '#ef4444',  # Red
    'grid': '#1e3a5f',
    'axis': '#475569',
    'accent': '#06b6d4',  # Cyan
}

# Zone thresholds by phase
ZONE_THRESHOLDS_BY_PHASE = {
    'powerplay': {  # 0-6 overs (0-36 balls)
        'target': 0.5,
        'acceptable': 1.0,
        'risky': 1.5
    },
    'middle_overs': {  # 7-16 overs (37-96 balls)
        'target': 1.0,
        'acceptable': 1.5,
        'risky': 2.5
    },
    'death_overs': {  # 17-20 overs (97-120 balls)
        'target': 1.0,
        'acceptable': 2.0,
        'risky': 2.5
    }
}

# Legacy zone thresholds (kept for backward compatibility)
ZONE_THRESHOLDS = {
    'target': 0.5,
    'acceptable': 1.5,
    'risky': 3.5,
}


def create_pressure_curve(
    pi_data: List[Dict],
    title: str = "Pressure Curve",
    show_zones: bool = True,
    show_wickets: bool = True,
    show_phase_markers: bool = True,
    height: int = 450,
    use_dynamic_zones: bool = True
) -> go.Figure:
    """
    Create a pressure curve visualization

    Args:
        pi_data: List of dicts with 'ball' and 'pressure_index' keys
        title: Chart title
        show_zones: Show zone threshold lines
        show_wickets: Highlight wicket falls
        show_phase_markers: Show powerplay/death overs markers
        height: Chart height in pixels
        use_dynamic_zones: Use dynamic phase-based zone thresholds

    Returns:
        Plotly Figure object
    """
    if not pi_data:
        return create_empty_chart("No data available", height)

    balls = [d['ball'] for d in pi_data]
    pi_values = [d['pressure_index'] for d in pi_data]
    wicket_balls = [d['ball'] for d in pi_data if d.get('is_wicket', False)]
    wicket_pis = [d['pressure_index'] for d in pi_data if d.get('is_wicket', False)]

    # Create figure
    fig = go.Figure()

    max_pi = max(pi_values) if pi_values else 4
    max_y = max(max_pi * 1.2, 6)
    max_x = max(balls) if balls else 120

    # Add zone backgrounds and threshold lines with dynamic phase-based zones
    if show_zones and use_dynamic_zones:
        # Powerplay phase (0-36 balls)
        pp_end = min(36, max_x)
        pp_zones = ZONE_THRESHOLDS_BY_PHASE['powerplay']

        # Middle overs phase (37-96 balls)
        mo_start = 37
        mo_end = min(96, max_x)
        mo_zones = ZONE_THRESHOLDS_BY_PHASE['middle_overs']

        # Death overs phase (97-120 balls)
        do_start = 97
        do_zones = ZONE_THRESHOLDS_BY_PHASE['death_overs']

        # Draw phase-specific zone lines
        # Powerplay zone lines (0-36 balls)
        if pp_end > 0:
            fig.add_shape(
                type="line",
                x0=0, x1=pp_end,
                y0=pp_zones['target'], y1=pp_zones['target'],
                line=dict(color=COLORS['target_zone'], dash='dash', width=2),
                layer="below"
            )
            fig.add_shape(
                type="line",
                x0=0, x1=pp_end,
                y0=pp_zones['acceptable'], y1=pp_zones['acceptable'],
                line=dict(color=COLORS['acceptable_zone'], dash='dash', width=2),
                layer="below"
            )
            fig.add_shape(
                type="line",
                x0=0, x1=pp_end,
                y0=pp_zones['risky'], y1=pp_zones['risky'],
                line=dict(color=COLORS['risky_zone'], dash='dash', width=2),
                layer="below"
            )

        # Middle overs zone lines (37-96 balls)
        if max_x > mo_start:
            fig.add_shape(
                type="line",
                x0=mo_start, x1=mo_end,
                y0=mo_zones['target'], y1=mo_zones['target'],
                line=dict(color=COLORS['target_zone'], dash='dash', width=2),
                layer="below"
            )
            fig.add_shape(
                type="line",
                x0=mo_start, x1=mo_end,
                y0=mo_zones['acceptable'], y1=mo_zones['acceptable'],
                line=dict(color=COLORS['acceptable_zone'], dash='dash', width=2),
                layer="below"
            )
            fig.add_shape(
                type="line",
                x0=mo_start, x1=mo_end,
                y0=mo_zones['risky'], y1=mo_zones['risky'],
                line=dict(color=COLORS['risky_zone'], dash='dash', width=2),
                layer="below"
            )

        # Death overs zone lines (97-120 balls)
        if max_x >= do_start:
            fig.add_shape(
                type="line",
                x0=do_start, x1=max_x,
                y0=do_zones['target'], y1=do_zones['target'],
                line=dict(color=COLORS['target_zone'], dash='dash', width=2),
                layer="below"
            )
            fig.add_shape(
                type="line",
                x0=do_start, x1=max_x,
                y0=do_zones['acceptable'], y1=do_zones['acceptable'],
                line=dict(color=COLORS['acceptable_zone'], dash='dash', width=2),
                layer="below"
            )
            fig.add_shape(
                type="line",
                x0=do_start, x1=max_x,
                y0=do_zones['risky'], y1=do_zones['risky'],
                line=dict(color=COLORS['risky_zone'], dash='dash', width=2),
                layer="below"
            )
    elif show_zones:
        # Legacy static zones
        # Target zone (0 - 0.5)
        fig.add_hrect(
            y0=0, y1=ZONE_THRESHOLDS['target'],
            fillcolor=COLORS['target_zone'], opacity=0.1,
            layer="below", line_width=0
        )

        # Acceptable zone (0.5 - 1.5)
        fig.add_hrect(
            y0=ZONE_THRESHOLDS['target'], y1=ZONE_THRESHOLDS['acceptable'],
            fillcolor=COLORS['acceptable_zone'], opacity=0.1,
            layer="below", line_width=0
        )

        # High risk zone (>2)
        fig.add_hrect(
            y0=2, y1=max_y,
            fillcolor=COLORS['risky_zone'], opacity=0.05,
            layer="below", line_width=0
        )

        # Zone threshold lines
        fig.add_hline(
            y=ZONE_THRESHOLDS['target'],
            line=dict(color=COLORS['target_zone'], dash='dash', width=1),
            annotation_text="Target Zone",
            annotation_position="right",
            annotation_font_color=COLORS['target_zone']
        )

        fig.add_hline(
            y=ZONE_THRESHOLDS['acceptable'],
            line=dict(color=COLORS['acceptable_zone'], dash='dash', width=1),
            annotation_text="Acceptable",
            annotation_position="right",
            annotation_font_color=COLORS['acceptable_zone']
        )

        fig.add_hline(
            y=2,
            line=dict(color=COLORS['risky_zone'], dash='dash', width=1),
            annotation_text="High Risk",
            annotation_position="right",
            annotation_font_color=COLORS['risky_zone']
        )
    
    # Add phase markers
    if show_phase_markers and balls:
        # Powerplay end (ball 36)
        if max(balls) >= 36:
            fig.add_vline(
                x=36, line=dict(color=COLORS['accent'], dash='dot', width=1),
                annotation_text="PP End",
                annotation_position="top",
                annotation_font_size=10,
                annotation_font_color=COLORS['accent']
            )
        
        # Death overs start (ball 96)
        if max(balls) >= 96:
            fig.add_vline(
                x=96, line=dict(color=COLORS['accent'], dash='dot', width=1),
                annotation_text="Death",
                annotation_position="top",
                annotation_font_size=10,
                annotation_font_color=COLORS['accent']
            )
    
    # Main pressure curve
    fig.add_trace(go.Scatter(
        x=balls,
        y=pi_values,
        mode='lines+markers',
        name='Pressure Index',
        line=dict(color=COLORS['pressure_line'], width=2),
        marker=dict(size=4, color=COLORS['pressure_line']),
        hovertemplate='Ball: %{x}<br>PI: %{y:.2f}<extra></extra>'
    ))

    # Wicket markers
    if show_wickets and wicket_balls:
        fig.add_trace(go.Scatter(
            x=wicket_balls,
            y=wicket_pis,
            mode='markers',
            name='Wicket Fall',
            marker=dict(
                size=10,
                color=COLORS['wicket_marker'],
                symbol='x',
                line=dict(width=2, color=COLORS['wicket_marker'])
            ),
            hovertemplate='Wicket at ball %{x}<br>PI: %{y:.2f}<extra></extra>'
        ))

    # Add zone legend traces (invisible lines just for legend)
    if show_zones and use_dynamic_zones:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='lines',
            name='Target Zone',
            line=dict(color=COLORS['target_zone'], dash='dash', width=2),
            showlegend=True
        ))
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='lines',
            name='Acceptable Zone',
            line=dict(color=COLORS['acceptable_zone'], dash='dash', width=2),
            showlegend=True
        ))
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='lines',
            name='High Risk Zone',
            line=dict(color=COLORS['risky_zone'], dash='dash', width=2),
            showlegend=True
        ))
    
    # Layout
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color=COLORS['text'], size=16),
            x=0.5
        ),
        xaxis=dict(
            title=dict(text="Balls", font=dict(color=COLORS['text_secondary'])),
            tickfont=dict(color=COLORS['text_secondary']),
            gridcolor=COLORS['grid'],
            linecolor=COLORS['axis'],
            showgrid=True,
            zeroline=False,
            range=[0, max(balls) + 5] if balls else [0, 120]
        ),
        yaxis=dict(
            title=dict(text="Pressure Index", font=dict(color=COLORS['text_secondary'])),
            tickfont=dict(color=COLORS['text_secondary']),
            gridcolor=COLORS['grid'],
            linecolor=COLORS['axis'],
            showgrid=True,
            zeroline=True,
            zerolinecolor=COLORS['grid'],
            range=[0, max(max(pi_values) * 1.2, 4) if pi_values else 4]
        ),
        plot_bgcolor=COLORS['card_bg'],
        paper_bgcolor=COLORS['background'],
        height=height,
        margin=dict(l=60, r=120, t=50, b=60),
        legend=dict(
            font=dict(color=COLORS['text_secondary']),
            bgcolor='rgba(17, 28, 50, 0.8)',
            bordercolor=COLORS['grid'],
            borderwidth=1
        ),
        hovermode='x unified'
    )
    
    return fig


def create_comparison_curve(
    pi_data_1: List[Dict],
    pi_data_2: List[Dict],
    label_1: str = "Match 1",
    label_2: str = "Match 2",
    title: str = "Pressure Curve Comparison",
    height: int = 500
) -> go.Figure:
    """
    Create a comparison chart with two pressure curves
    """
    fig = go.Figure()
    
    # Add zone lines
    fig.add_hline(y=0.5, line=dict(color=COLORS['target_zone'], dash='dash', width=1))
    fig.add_hline(y=1.5, line=dict(color=COLORS['acceptable_zone'], dash='dash', width=1))
    fig.add_hline(y=2, line=dict(color=COLORS['risky_zone'], dash='dash', width=1))
    
    # First curve
    if pi_data_1:
        balls_1 = [d['ball'] for d in pi_data_1]
        pi_1 = [d['pressure_index'] for d in pi_data_1]
        wicket_balls_1 = [d['ball'] for d in pi_data_1 if d.get('is_wicket', False)]
        wicket_pis_1 = [d['pressure_index'] for d in pi_data_1 if d.get('is_wicket', False)]
        
        fig.add_trace(go.Scatter(
            x=balls_1, y=pi_1,
            mode='lines+markers',
            name=label_1,
            line=dict(color=COLORS['pressure_line'], width=2),
            marker=dict(size=4),
            hovertemplate=f'{label_1}<br>Ball: %{{x}}<br>PI: %{{y:.2f}}<extra></extra>'
        ))
        
        if wicket_balls_1:
            fig.add_trace(go.Scatter(
                x=wicket_balls_1, y=wicket_pis_1,
                mode='markers',
                name=f'{label_1} Wickets',
                marker=dict(size=8, color=COLORS['pressure_line'], symbol='x'),
                showlegend=False
            ))
    
    # Second curve
    if pi_data_2:
        balls_2 = [d['ball'] for d in pi_data_2]
        pi_2 = [d['pressure_index'] for d in pi_data_2]
        wicket_balls_2 = [d['ball'] for d in pi_data_2 if d.get('is_wicket', False)]
        wicket_pis_2 = [d['pressure_index'] for d in pi_data_2 if d.get('is_wicket', False)]
        
        fig.add_trace(go.Scatter(
            x=balls_2, y=pi_2,
            mode='lines+markers',
            name=label_2,
            line=dict(color=COLORS['acceptable_zone'], width=2),
            marker=dict(size=4),
            hovertemplate=f'{label_2}<br>Ball: %{{x}}<br>PI: %{{y:.2f}}<extra></extra>'
        ))
        
        if wicket_balls_2:
            fig.add_trace(go.Scatter(
                x=wicket_balls_2, y=wicket_pis_2,
                mode='markers',
                name=f'{label_2} Wickets',
                marker=dict(size=8, color=COLORS['acceptable_zone'], symbol='x'),
                showlegend=False
            ))
    
    # Layout
    max_balls = 120
    max_pi = 4
    
    if pi_data_1:
        max_balls = max(max_balls, max(d['ball'] for d in pi_data_1))
        max_pi = max(max_pi, max(d['pressure_index'] for d in pi_data_1))
    if pi_data_2:
        max_balls = max(max_balls, max(d['ball'] for d in pi_data_2))
        max_pi = max(max_pi, max(d['pressure_index'] for d in pi_data_2))
    
    fig.update_layout(
        title=dict(text=title, font=dict(color=COLORS['text'], size=16), x=0.5),
        xaxis=dict(
            title=dict(text="Balls", font=dict(color=COLORS['text_secondary'])),
            tickfont=dict(color=COLORS['text_secondary']),
            gridcolor=COLORS['grid'],
            range=[0, max_balls + 5]
        ),
        yaxis=dict(
            title=dict(text="Pressure Index", font=dict(color=COLORS['text_secondary'])),
            tickfont=dict(color=COLORS['text_secondary']),
            gridcolor=COLORS['grid'],
            range=[0, max_pi * 1.2]
        ),
        plot_bgcolor=COLORS['card_bg'],
        paper_bgcolor=COLORS['background'],
        height=height,
        legend=dict(
            font=dict(color=COLORS['text_secondary']),
            bgcolor='rgba(17, 28, 50, 0.8)'
        ),
        hovermode='x unified'
    )
    
    return fig


def create_live_comparison_curve(
    past_pi_data: List[Dict],
    live_pi_data: List[Dict],
    past_label: str = "Past Match",
    title: str = "Live vs Past Match Comparison",
    height: int = 500
) -> go.Figure:
    """
    Create comparison chart for live match vs past match
    Live data shown with animated marker for current position
    """
    fig = create_comparison_curve(
        pi_data_1=past_pi_data,
        pi_data_2=live_pi_data,
        label_1=past_label,
        label_2="Live Match",
        title=title,
        height=height
    )
    
    # Add current position marker for live match
    if live_pi_data:
        current = live_pi_data[-1]
        fig.add_trace(go.Scatter(
            x=[current['ball']],
            y=[current['pressure_index']],
            mode='markers',
            name='Current Position',
            marker=dict(
                size=15,
                color=COLORS['accent'],
                symbol='circle',
                line=dict(width=2, color='white')
            ),
            hovertemplate=f'Current Position<br>Ball: {current["ball"]}<br>PI: {current["pressure_index"]:.2f}<extra></extra>'
        ))
    
    return fig


def create_over_summary_chart(
    over_data: List[Dict],
    title: str = "Over-by-Over Summary",
    height: int = 350
) -> go.Figure:
    """
    Create bar chart showing runs and wickets per over
    """
    if not over_data:
        return create_empty_chart("No over data available", height)
    
    overs = [d['over'] for d in over_data]
    runs = [d['runs'] for d in over_data]
    wickets = [d['wickets'] for d in over_data]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Runs bars
    fig.add_trace(
        go.Bar(
            x=overs, y=runs,
            name='Runs',
            marker_color=COLORS['pressure_line'],
            hovertemplate='Over %{x}<br>Runs: %{y}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Wickets as markers
    wicket_overs = [o for o, w in zip(overs, wickets) if w > 0]
    wicket_counts = [w for w in wickets if w > 0]
    
    if wicket_overs:
        fig.add_trace(
            go.Scatter(
                x=wicket_overs, y=wicket_counts,
                mode='markers',
                name='Wickets',
                marker=dict(size=12, color=COLORS['wicket_marker'], symbol='x'),
                hovertemplate='Over %{x}<br>Wickets: %{y}<extra></extra>'
            ),
            secondary_y=True
        )
    
    fig.update_layout(
        title=dict(text=title, font=dict(color=COLORS['text'], size=14), x=0.5),
        xaxis=dict(
            title=dict(text="Over", font=dict(color=COLORS['text_secondary'])),
            tickfont=dict(color=COLORS['text_secondary']),
            gridcolor=COLORS['grid'],
            dtick=2
        ),
        yaxis=dict(
            title=dict(text="Runs", font=dict(color=COLORS['text_secondary'])),
            tickfont=dict(color=COLORS['text_secondary']),
            gridcolor=COLORS['grid']
        ),
        yaxis2=dict(
            title=dict(text="Wickets", font=dict(color=COLORS['wicket_marker'])),
            tickfont=dict(color=COLORS['wicket_marker']),
            range=[0, 5]
        ),
        plot_bgcolor=COLORS['card_bg'],
        paper_bgcolor=COLORS['background'],
        height=height,
        legend=dict(
            font=dict(color=COLORS['text_secondary']),
            bgcolor='rgba(17, 28, 50, 0.8)',
            orientation='h',
            yanchor='bottom',
            y=1.02
        ),
        bargap=0.2
    )
    
    return fig


def create_pi_gauge(
    pi_value: float,
    phase: str = "middle_overs",
    height: int = 200
) -> go.Figure:
    """
    Create a gauge chart showing current PI with zone coloring
    """
    # Determine color based on zone
    if pi_value < 0.5:
        color = COLORS['target_zone']
        zone = "Target Zone"
    elif pi_value < 1.5:
        color = COLORS['acceptable_zone']
        zone = "Acceptable"
    elif pi_value < 3.5:
        color = COLORS['risky_zone']
        zone = "Risky"
    else:
        color = COLORS['avoid_zone']
        zone = "High Pressure"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pi_value,
        number=dict(
            font=dict(color=COLORS['text'], size=36),
            suffix=""
        ),
        gauge=dict(
            axis=dict(
                range=[0, 6],
                tickfont=dict(color=COLORS['text_secondary']),
                tickcolor=COLORS['text_secondary']
            ),
            bar=dict(color=color),
            bgcolor=COLORS['card_bg'],
            bordercolor=COLORS['grid'],
            steps=[
                dict(range=[0, 0.5], color=f"rgba(16, 185, 129, 0.3)"),
                dict(range=[0.5, 1.5], color=f"rgba(245, 158, 11, 0.3)"),
                dict(range=[1.5, 3.5], color=f"rgba(239, 68, 68, 0.2)"),
                dict(range=[3.5, 6], color=f"rgba(220, 38, 38, 0.3)")
            ],
            threshold=dict(
                line=dict(color=COLORS['text'], width=2),
                thickness=0.75,
                value=pi_value
            )
        ),
        title=dict(
            text=zone,
            font=dict(color=color, size=14)
        )
    ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['background'],
        height=height,
        margin=dict(l=30, r=30, t=50, b=20)
    )
    
    return fig


def create_empty_chart(message: str, height: int = 300) -> go.Figure:
    """Create an empty chart with a message"""
    fig = go.Figure()
    
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color=COLORS['text_secondary'])
    )
    
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor=COLORS['card_bg'],
        paper_bgcolor=COLORS['background'],
        height=height
    )
    
    return fig


def get_zone_color(zone: str) -> str:
    """Get color for a zone"""
    zone_colors = {
        'target': COLORS['target_zone'],
        'acceptable': COLORS['acceptable_zone'],
        'risky': COLORS['risky_zone'],
        'avoid': COLORS['avoid_zone']
    }
    return zone_colors.get(zone, COLORS['text_secondary'])
