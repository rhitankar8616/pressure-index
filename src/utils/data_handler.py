"""
Data Handler Module
Handles loading and processing of historical match data from CSV
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os


class MatchDataHandler:
    """Class to handle historical match data from CSV"""

    def __init__(self, csv_path: str = None, df: pd.DataFrame = None):
        """
        Initialize with path to the pi-t20.csv file or a DataFrame directly

        Args:
            csv_path: Path to CSV file (optional if df is provided)
            df: Pre-loaded DataFrame (optional if csv_path is provided)

        Expected columns:
        - date: Match date (YYYY-MM-DD)
        - p_match: Match ID
        - winner: Winning team
        - target: Target score
        - max_balls: Total balls (usually 120)
        - team_bowl: Bowling team
        - inns_rrr: Required run rate at that ball
        - inns_wkts: Wickets lost
        - inns_balls_rem: Balls remaining
        - inns_runs_rem: Runs remaining
        - ground: Venue
        - bat: Batsman name
        - team_bat: Batting team
        - score: Runs scored on this ball
        - out: True/False if batsman was dismissed
        - bowl: Bowler name
        - competition: Competition name
        """
        self.csv_path = csv_path
        self.df = df
        if self.df is None:
            self._load_data()
        else:
            self._preprocess_data()

    def _load_data(self):
        """Load the CSV data"""
        if self.csv_path and os.path.exists(self.csv_path):
            self.df = pd.read_csv(self.csv_path)
            self._preprocess_data()
        else:
            if self.csv_path:
                print(f"Warning: Data file not found at {self.csv_path}")
            self.df = pd.DataFrame()
    
    def _preprocess_data(self):
        """Preprocess the loaded data"""
        if self.df.empty:
            return
        
        # Convert date to datetime
        self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')
        
        # Calculate balls faced from balls remaining
        self.df['balls_faced'] = self.df['max_balls'] - self.df['inns_balls_rem']
        
        # Calculate runs scored
        self.df['runs_scored'] = self.df['target'] - self.df['inns_runs_rem']
        
        # Calculate over number
        self.df['over'] = (self.df['balls_faced'] - 1) // 6 + 1
        self.df['ball_in_over'] = ((self.df['balls_faced'] - 1) % 6) + 1
        
        # Sort by match and ball
        self.df = self.df.sort_values(['p_match', 'balls_faced'])
    
    def get_unique_teams(self) -> Tuple[List[str], List[str]]:
        """Get lists of unique batting and bowling teams"""
        if self.df.empty:
            return [], []
        
        batting_teams = sorted(self.df['team_bat'].dropna().unique().tolist())
        bowling_teams = sorted(self.df['team_bowl'].dropna().unique().tolist())
        
        return batting_teams, bowling_teams
    
    def get_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get the date range of available data"""
        if self.df.empty:
            return None, None
        
        min_date = self.df['date'].min()
        max_date = self.df['date'].max()
        
        return min_date, max_date
    
    def get_unique_competitions(self) -> List[str]:
        """Get list of unique competitions"""
        if self.df.empty:
            return []
        
        return sorted(self.df['competition'].dropna().unique().tolist())
    
    def get_unique_grounds(self) -> List[str]:
        """Get list of unique grounds/venues"""
        if self.df.empty:
            return []
        
        return sorted(self.df['ground'].dropna().unique().tolist())
    
    def search_matches(self, start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      batting_team: Optional[str] = None,
                      bowling_team: Optional[str] = None,
                      competition: Optional[str] = None,
                      ground: Optional[str] = None) -> List[Dict]:
        """
        Search for matches based on criteria
        
        Returns list of match summaries
        """
        if self.df.empty:
            return []
        
        mask = pd.Series([True] * len(self.df))
        
        if start_date:
            mask &= self.df['date'] >= start_date
        
        if end_date:
            mask &= self.df['date'] <= end_date
        
        if batting_team and batting_team != 'All':
            mask &= self.df['team_bat'] == batting_team
        
        if bowling_team and bowling_team != 'All':
            mask &= self.df['team_bowl'] == bowling_team
        
        if competition and competition != 'All':
            mask &= self.df['competition'] == competition
        
        if ground and ground != 'All':
            mask &= self.df['ground'] == ground
        
        filtered = self.df[mask]
        
        # Get unique matches
        match_ids = filtered['p_match'].unique()
        
        matches = []
        for match_id in match_ids:
            match_data = filtered[filtered['p_match'] == match_id]
            if match_data.empty:
                continue
            
            first_row = match_data.iloc[0]
            last_row = match_data.iloc[-1]
            
            matches.append({
                'match_id': match_id,
                'date': first_row['date'],
                'batting_team': first_row['team_bat'],
                'bowling_team': first_row['team_bowl'],
                'target': first_row['target'],
                'ground': first_row['ground'],
                'competition': first_row['competition'],
                'final_score': int(last_row['runs_scored']),
                'final_wickets': int(last_row['inns_wkts']),
                'result': 'Won' if last_row['inns_runs_rem'] <= 0 else 'Lost'
            })
        
        return matches
    
    def get_match_ball_by_ball(self, match_id: int) -> pd.DataFrame:
        """
        Get ball-by-ball data for a specific match
        
        Returns DataFrame with columns for PI calculation
        """
        if self.df.empty:
            return pd.DataFrame()
        
        match_data = self.df[self.df['p_match'] == match_id].copy()
        
        if match_data.empty:
            return pd.DataFrame()
        
        # Sort by balls faced
        match_data = match_data.sort_values('balls_faced')
        
        # Detect wicket falls by comparing consecutive wicket counts
        match_data['is_wicket'] = match_data['inns_wkts'].diff().fillna(0) > 0
        
        return match_data
    
    def get_match_summary(self, match_id: int) -> Optional[Dict]:
        """Get summary information for a specific match"""
        if self.df.empty:
            return None
        
        match_data = self.df[self.df['p_match'] == match_id]
        
        if match_data.empty:
            return None
        
        first_row = match_data.iloc[0]
        last_row = match_data.iloc[-1]
        
        return {
            'match_id': match_id,
            'date': first_row['date'],
            'batting_team': first_row['team_bat'],
            'bowling_team': first_row['team_bowl'],
            'target': int(first_row['target']),
            'max_balls': int(first_row['max_balls']),
            'ground': first_row['ground'],
            'competition': first_row['competition'],
            'final_score': int(last_row['runs_scored']),
            'final_wickets': int(last_row['inns_wkts']),
            'balls_faced': int(last_row['balls_faced']),
            'result': 'Won' if last_row['inns_runs_rem'] <= 0 else 'Lost'
        }
    
    def get_over_summary(self, match_id: int) -> List[Dict]:
        """
        Get over-by-over summary for a match
        
        Returns list of dicts with runs and wickets per over
        """
        match_data = self.get_match_ball_by_ball(match_id)
        
        if match_data.empty:
            return []
        
        over_summary = []
        
        for over_num in range(1, 21):
            over_data = match_data[match_data['over'] == over_num]
            
            if over_data.empty:
                continue
            
            start_runs = over_data.iloc[0]['runs_scored'] - 1 if over_data.iloc[0]['balls_faced'] > 1 else 0
            end_runs = over_data.iloc[-1]['runs_scored']
            runs_in_over = end_runs - start_runs
            
            wickets_in_over = over_data['is_wicket'].sum()
            
            over_summary.append({
                'over': over_num,
                'runs': int(runs_in_over),
                'wickets': int(wickets_in_over),
                'cumulative_runs': int(end_runs),
                'cumulative_wickets': int(over_data.iloc[-1]['inns_wkts'])
            })
        
        return over_summary
    
    def calculate_pi_for_match(self, match_id: int, pi_calculator) -> List[Dict]:
        """
        Calculate Pressure Index for each ball of a match
        
        Args:
            match_id: Match ID
            pi_calculator: PressureIndexCalculator instance
        
        Returns:
            List of dicts with PI values for each ball
        """
        match_data = self.get_match_ball_by_ball(match_id)
        
        if match_data.empty:
            return []
        
        target = match_data.iloc[0]['target']
        max_balls = match_data.iloc[0]['max_balls']
        
        pi_values = []
        
        for _, row in match_data.iterrows():
            pi = pi_calculator.calculate_pressure_index(
                target=int(target),
                runs_scored=int(row['runs_scored']),
                balls_faced=int(row['balls_faced']),
                wickets_lost=int(row['inns_wkts']),
                total_balls=int(max_balls)
            )
            
            pi_values.append({
                'ball': int(row['balls_faced']),
                'over': int(row['over']),
                'ball_in_over': int(row['ball_in_over']),
                'runs': int(row['runs_scored']),
                'wickets': int(row['inns_wkts']),
                'pressure_index': pi,
                'is_wicket': bool(row['is_wicket']),
                'batsman': row.get('bat', ''),
                'bowler': row.get('bowl', ''),
                'required_run_rate': row.get('inns_rrr', 0)
            })
        
        return pi_values


def get_data_handler() -> Optional[MatchDataHandler]:
    """Get the data handler instance"""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(base_path, 'data', 'pi-t20.csv')

    if os.path.exists(csv_path):
        return MatchDataHandler(csv_path)
    return None
