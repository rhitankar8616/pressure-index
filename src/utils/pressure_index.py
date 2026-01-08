"""
Pressure Index Calculation Module
Based on: "Applications of higher order Markov models and Pressure Index 
to strategize controlled run chases in Twenty20 cricket"
Authors: Rhitankar Bandyopadhyay & Dibyojyoti Bhattacharjee
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict
import os

# Wicket weights as per Lemmer (2015) - Table 1 from the paper
WICKET_WEIGHTS = {
    1: 1.30,
    2: 1.35,
    3: 1.40,
    4: 1.45,
    5: 1.38,
    6: 1.18,
    7: 0.98,
    8: 0.79,
    9: 0.59,
    10: 0.39,
    11: 0.19
}

# Phase-wise Gamma distribution parameters (Table 10 from paper)
GAMMA_PARAMS = {
    'powerplay': {'shape': 38.276, 'rate': 28.931},
    'middle_overs': {'shape': 18.447, 'rate': 10.62},
    'death_overs': {'shape': 3.667, 'rate': 1.286}
}

# Phase-wise PI thresholds for strategic recommendations (Table 19 from paper)
STRATEGIC_ZONES = {
    'powerplay': {
        'target': (0, 0.5),
        'acceptable': (0.5, 1.0),
        'risky': (1.0, 1.5),
        'avoid': (1.5, float('inf'))
    },
    'middle_overs': {
        'target': (0, 1.0),
        'acceptable': (1.0, 1.5),
        'risky': (1.5, 2.5),
        'avoid': (2.5, float('inf'))
    },
    'death_overs': {
        'target': (0, 1.0),
        'acceptable': (1.0, 2.5),
        'risky': (2.5, 3.5),
        'avoid': (3.5, float('inf'))
    }
}


class DuckworthLewisTable:
    """Class to handle Duckworth-Lewis resource calculations"""
    
    def __init__(self, csv_path: str):
        """Load the D/L table from CSV"""
        self.df = pd.read_csv(csv_path)
        self._build_lookup()
    
    def _build_lookup(self):
        """Build a lookup dictionary for fast resource retrieval"""
        self.lookup = {}
        for _, row in self.df.iterrows():
            overs_left = int(row['overs_left'])
            for wickets in range(10):
                col_name = f'wickets_{wickets}'
                self.lookup[(overs_left, wickets)] = row[col_name]
    
    def get_resources_remaining(self, overs_left: float, wickets_lost: int) -> float:
        """
        Get the percentage of resources remaining
        
        Args:
            overs_left: Number of overs remaining (can be fractional)
            wickets_lost: Number of wickets lost (0-9)
        
        Returns:
            Percentage of resources remaining
        """
        # Clamp wickets to valid range
        wickets_lost = max(0, min(9, wickets_lost))
        
        # Handle fractional overs by interpolation
        overs_floor = int(overs_left)
        overs_ceil = overs_floor + 1
        fraction = overs_left - overs_floor
        
        # Clamp overs to valid range
        overs_floor = max(0, min(20, overs_floor))
        overs_ceil = max(0, min(20, overs_ceil))
        
        if overs_floor == 0:
            return 0.0
        
        # Get resources for floor and ceiling
        res_floor = self.lookup.get((overs_floor, wickets_lost), 0.0)
        res_ceil = self.lookup.get((overs_ceil, wickets_lost), 0.0)
        
        # Linear interpolation
        if overs_ceil == overs_floor:
            return res_floor
        
        return res_floor + fraction * (res_ceil - res_floor)
    
    def get_resources_used(self, balls_faced: int, wickets_lost: int, total_balls: int = 120) -> float:
        """
        Calculate the percentage of resources used
        
        Args:
            balls_faced: Number of balls faced so far
            wickets_lost: Number of wickets lost
            total_balls: Total balls in innings (default 120 for T20)
        
        Returns:
            Percentage of resources used (RU)
        """
        overs_left = (total_balls - balls_faced) / 6.0
        resources_remaining = self.get_resources_remaining(overs_left, wickets_lost)
        resources_used = 100.0 - resources_remaining
        return max(0.0, resources_used)


class PressureIndexCalculator:
    """
    Calculate Pressure Index as per Bhattacharjee and Lemmer (2016)
    
    Formula (Equation 6 from paper):
    PI = (CRRR/IRRR) × (1/2) × [e^(RU/100) + e^(Σwi/11)]
    """
    
    def __init__(self, dl_table: DuckworthLewisTable):
        self.dl_table = dl_table
    
    def calculate_initial_required_run_rate(self, target: int, total_balls: int = 120) -> float:
        """
        Calculate Initial Required Run Rate (IRRR)
        IRRR = (T × 6) / B
        """
        if total_balls == 0:
            return 0.0
        return (target * 6) / total_balls
    
    def calculate_current_required_run_rate(self, target: int, runs_scored: int, 
                                             balls_faced: int, total_balls: int = 120) -> float:
        """
        Calculate Current Required Run Rate (CRRR)
        CRRR = ((T - R') × 6) / (B - B')
        """
        runs_remaining = target - runs_scored
        balls_remaining = total_balls - balls_faced
        
        if balls_remaining <= 0:
            return 0.0 if runs_remaining <= 0 else float('inf')
        
        return (runs_remaining * 6) / balls_remaining
    
    def calculate_wicket_weight_sum(self, wickets_lost: int) -> float:
        """
        Calculate sum of wicket weights (Σwi) for fallen wickets
        Uses Lemmer (2015) weights from Table 1
        """
        if wickets_lost <= 0:
            return 0.0
        
        # Sum weights for wickets 1 to wickets_lost
        total = sum(WICKET_WEIGHTS.get(i, 0) for i in range(1, min(wickets_lost + 1, 12)))
        return total
    
    def calculate_pressure_index(self, target: int, runs_scored: int, 
                                  balls_faced: int, wickets_lost: int,
                                  total_balls: int = 120) -> float:
        """
        Calculate the Pressure Index (PI)
        
        Formula: PI = (CRRR/IRRR) × (1/2) × [e^(RU/100) + e^(Σwi/11)]
        
        Args:
            target: Target score to chase
            runs_scored: Runs scored so far
            balls_faced: Balls faced so far
            wickets_lost: Wickets lost (0-10)
            total_balls: Total balls in innings (default 120)
        
        Returns:
            Pressure Index value (PI+ = max(PI, 0))
        """
        # Check if target achieved
        if runs_scored >= target:
            return 0.0
        
        # Check if all out
        if wickets_lost >= 10:
            return float('inf')
        
        # Calculate components
        irrr = self.calculate_initial_required_run_rate(target, total_balls)
        crrr = self.calculate_current_required_run_rate(target, runs_scored, balls_faced, total_balls)
        
        if irrr == 0:
            return 0.0
        
        ci = crrr / irrr  # CI ratio
        
        # Get Resources Used
        ru = self.dl_table.get_resources_used(balls_faced, wickets_lost, total_balls)
        
        # Calculate wicket weight sum
        sum_wi = self.calculate_wicket_weight_sum(wickets_lost)
        
        # Calculate PI using formula (6)
        exp_ru = np.exp(ru / 100.0)
        exp_wi = np.exp(sum_wi / 11.0)
        
        pi = ci * 0.5 * (exp_ru + exp_wi)
        
        # Return PI+ (censored at 0)
        return max(0.0, pi)
    
    def calculate_ball_by_ball_pi(self, target: int, ball_data: List[Dict], 
                                   total_balls: int = 120) -> List[Dict]:
        """
        Calculate PI for each ball in the innings
        
        Args:
            target: Target score
            ball_data: List of dicts with 'runs_scored', 'wickets_lost' for each ball
            total_balls: Total balls in innings
        
        Returns:
            List of dicts with PI values added
        """
        results = []
        cumulative_runs = 0
        cumulative_wickets = 0
        
        for i, ball in enumerate(ball_data):
            ball_num = i + 1
            cumulative_runs += ball.get('runs', 0)
            if ball.get('wicket', False):
                cumulative_wickets += 1
            
            pi = self.calculate_pressure_index(
                target=target,
                runs_scored=cumulative_runs,
                balls_faced=ball_num,
                wickets_lost=cumulative_wickets,
                total_balls=total_balls
            )
            
            results.append({
                'ball': ball_num,
                'over': (ball_num - 1) // 6 + 1,
                'ball_in_over': ((ball_num - 1) % 6) + 1,
                'runs': cumulative_runs,
                'wickets': cumulative_wickets,
                'pressure_index': pi,
                'is_wicket': ball.get('wicket', False)
            })
        
        return results


def get_phase(over: int) -> str:
    """
    Determine the phase of the innings based on over number
    
    Args:
        over: Over number (1-20)
    
    Returns:
        Phase name: 'powerplay', 'middle_overs', or 'death_overs'
    """
    if over <= 6:
        return 'powerplay'
    elif over <= 16:
        return 'middle_overs'
    else:
        return 'death_overs'


def get_phase_display_name(phase: str) -> str:
    """Get display name for phase"""
    names = {
        'powerplay': 'Powerplay',
        'middle_overs': 'Middle Overs',
        'death_overs': 'Death Overs'
    }
    return names.get(phase, phase.title())


def get_zone_for_pi(pi: float, phase: str) -> str:
    """
    Determine the zone for a given PI value based on phase
    
    Args:
        pi: Pressure Index value
        phase: Phase of innings
    
    Returns:
        Zone name: 'target', 'acceptable', 'risky', or 'avoid'
    """
    zones = STRATEGIC_ZONES.get(phase, STRATEGIC_ZONES['middle_overs'])
    
    for zone_name, (low, high) in zones.items():
        if low <= pi < high:
            return zone_name
    
    return 'avoid'


def calculate_required_runs_for_zone(current_pi: float, target: int, runs_scored: int,
                                      balls_faced: int, wickets_lost: int,
                                      balls_ahead: int, phase: str,
                                      dl_table: DuckworthLewisTable,
                                      zone: str = 'target') -> Optional[int]:
    """
    Calculate how many runs needed in next N balls to reach a specific zone
    
    Args:
        current_pi: Current Pressure Index
        target: Target score
        runs_scored: Current runs scored
        balls_faced: Balls faced so far
        wickets_lost: Wickets lost
        balls_ahead: Number of balls to look ahead
        phase: Current phase
        dl_table: Duckworth-Lewis table
        zone: Target zone ('target', 'acceptable', 'risky')
    
    Returns:
        Required runs to reach the zone, or None if not achievable
    """
    zones = STRATEGIC_ZONES.get(phase, STRATEGIC_ZONES['middle_overs'])
    zone_bounds = zones.get(zone)
    
    if not zone_bounds:
        return None
    
    target_pi = zone_bounds[1]  # Upper bound of zone
    
    # Binary search for required runs
    calc = PressureIndexCalculator(dl_table)
    new_balls = balls_faced + balls_ahead
    
    # Check if target is already achieved
    runs_remaining = target - runs_scored
    if runs_remaining <= 0:
        return 0
    
    # Check maximum possible (all runs needed)
    for runs_needed in range(0, runs_remaining + 1):
        new_runs = runs_scored + runs_needed
        new_pi = calc.calculate_pressure_index(
            target=target,
            runs_scored=new_runs,
            balls_faced=new_balls,
            wickets_lost=wickets_lost
        )
        
        if new_pi < target_pi:
            return runs_needed
    
    return None  # Not achievable


def calculate_strategic_projections(target: int, runs_scored: int, balls_faced: int,
                                     wickets_lost: int, dl_table: DuckworthLewisTable,
                                     total_balls: int = 120) -> Dict:
    """
    Calculate strategic projections for next 1, 2, 3 overs
    
    Returns dict with required runs for each zone and time horizon
    """
    calc = PressureIndexCalculator(dl_table)
    current_pi = calc.calculate_pressure_index(target, runs_scored, balls_faced, wickets_lost, total_balls)
    
    current_over = (balls_faced // 6) + 1
    phase = get_phase(current_over)
    
    projections = {
        'current_pi': current_pi,
        'phase': phase,
        'horizons': {}
    }
    
    for overs_ahead, label in [(1, 'next_1_over'), (2, 'next_2_overs'), (3, 'next_3_overs')]:
        balls_ahead = overs_ahead * 6
        new_balls = balls_faced + balls_ahead
        
        if new_balls > total_balls:
            balls_ahead = total_balls - balls_faced
            if balls_ahead <= 0:
                continue
        
        horizon_data = {'balls': balls_ahead, 'zones': {}}
        
        # Calculate for each zone
        for zone in ['target', 'acceptable', 'risky']:
            runs_needed = calculate_required_runs_for_zone(
                current_pi=current_pi,
                target=target,
                runs_scored=runs_scored,
                balls_faced=balls_faced,
                wickets_lost=wickets_lost,
                balls_ahead=balls_ahead,
                phase=phase,
                dl_table=dl_table,
                zone=zone
            )
            
            if runs_needed is not None:
                rpo = (runs_needed / balls_ahead) * 6 if balls_ahead > 0 else 0
                horizon_data['zones'][zone] = {
                    'runs': runs_needed,
                    'rpo': round(rpo, 2),
                    'achievable': True
                }
            else:
                horizon_data['zones'][zone] = {
                    'runs': None,
                    'rpo': None,
                    'achievable': False
                }
        
        projections['horizons'][label] = horizon_data
    
    return projections


# Load default DL table
def get_default_dl_table() -> DuckworthLewisTable:
    """Get the default Duckworth-Lewis table"""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(base_path, 'data', 'duckworth_lewis_table.csv')
    return DuckworthLewisTable(csv_path)
