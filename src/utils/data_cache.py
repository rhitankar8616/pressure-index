"""
Centralized Data Cache
Ensures data is loaded and processed only once across all pages
"""

import streamlit as st
import pandas as pd
import os
from src.utils.csv_loader import load_csv_data
from src.utils.pressure_index import PressureIndexCalculator, DuckworthLewisTable


@st.cache_data(show_spinner=False)
def get_processed_data() -> pd.DataFrame:
    """
    Load and process the CSV data with all calculations done once
    This function is cached so it only runs once per session

    Returns:
        Fully processed DataFrame with all derived columns and PI values
    """
    # Load raw data
    df = load_csv_data()

    # Calculate derived columns
    df['ball'] = df['max_balls'] - df['inns_balls_rem']
    df['runs_scored_cumulative'] = df['target'] - df['inns_runs_rem']

    # Sort by match and ball
    df = df.sort_values(['p_match', 'ball'])

    # Use the new 'score' column for runs scored on this ball
    df['runs_scored'] = df['score'].fillna(0).astype(int)

    # Use the new 'out' column for wickets (True = out, False = not out)
    df['is_wicket'] = df['out'].fillna(False).astype(bool)

    # Calculate pressure index using DL table
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dl_table_path = os.path.join(base_path, 'data', 'duckworth_lewis_table.csv')
    dl_table = DuckworthLewisTable(dl_table_path)
    pi_calc = PressureIndexCalculator(dl_table)

    # Calculate PI for each row
    pi_values = []
    for _, row in df.iterrows():
        try:
            pi = pi_calc.calculate_pressure_index(
                target=int(row['target']),
                runs_scored=int(row['runs_scored_cumulative']),
                balls_faced=int(row['ball']),
                wickets_lost=int(row['inns_wkts']),
                total_balls=int(row['max_balls'])
            )
            pi_values.append(pi)
        except:
            pi_values.append(0.0)

    df['pressure_index'] = pi_values

    # Rename columns to match our expected format
    df = df.rename(columns={
        'bat': 'batsman',
        'team_bat': 'team',
        'team_bowl': 'opposition',
        'ground': 'venue',
        'p_match': 'match_id'
    })

    return df
