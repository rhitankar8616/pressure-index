"""
CSV Loader Utility
Handles loading large CSV files from Dropbox
"""

import os
import pandas as pd
import streamlit as st
import requests
from pathlib import Path
from io import StringIO

# Dropbox direct download link for pi-t20.csv
DROPBOX_CSV_URL = "https://www.dropbox.com/scl/fi/ngtum2qeh8q727dlwfpxj/pi-t20.csv?rlkey=vjt63fwe4jzb6ewvilorl0252&st=12ydinys&dl=1"

# Local cache path (optional - for faster subsequent loads)
CACHE_DIR = Path.home() / ".cache" / "pressure_index"
CACHE_FILE = CACHE_DIR / "pi-t20.csv"


@st.cache_data(ttl=86400)  # Cache for 24 hours
def load_csv_from_dropbox(url: str = DROPBOX_CSV_URL) -> pd.DataFrame:
    """
    Load CSV from Dropbox URL with caching

    Args:
        url: Direct download URL from Dropbox

    Returns:
        pandas DataFrame with the CSV data
    """
    # Try to load from local cache first if it exists
    if CACHE_FILE.exists():
        print(f"Loading CSV from cache: {CACHE_FILE}")
        try:
            df = pd.read_csv(CACHE_FILE)
            return df
        except Exception as e:
            print(f"Warning: Cache file corrupted, will re-download: {e}")

    # Try to load from local data folder (for development)
    local_path = Path(__file__).parent.parent.parent / "data" / "pi-t20.csv"
    if local_path.exists():
        print(f"Loading CSV from local file: {local_path}")
        try:
            df = pd.read_csv(local_path)
            # Cache it for future use
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                df.to_csv(CACHE_FILE, index=False)
                print(f"Cached local CSV to: {CACHE_FILE}")
            except:
                pass
            return df
        except Exception as e:
            print(f"Warning: Could not load local file: {e}")

    # Download from Dropbox
    print(f"Downloading CSV from Dropbox...")

    try:
        # Use requests library which handles SSL certificates better
        response = requests.get(url, timeout=300, verify=True)
        response.raise_for_status()

        # Read CSV from response content
        df = pd.read_csv(StringIO(response.text))

        # Save to cache for future use
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            df.to_csv(CACHE_FILE, index=False)
            print(f"Cached CSV to: {CACHE_FILE}")
        except Exception as e:
            print(f"Warning: Could not cache CSV file: {e}")

        return df

    except requests.exceptions.SSLError as e:
        error_msg = (
            "SSL certificate error when downloading from Dropbox.\n\n"
            "**For local development on macOS:**\n"
            "1. Run: /Applications/Python\\ 3.XX/Install\\ Certificates.command\n"
            "   (Replace 3.XX with your Python version)\n"
            "2. Or run: pip install --upgrade certifi\n\n"
            "**Alternative:** Place pi-t20.csv in the data/ folder for local testing.\n\n"
            f"Error: {str(e)}"
        )
        raise Exception(error_msg)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error downloading from Dropbox: {str(e)}")
    except Exception as e:
        raise Exception(f"Error loading CSV from Dropbox: {str(e)}")


def get_csv_path() -> str:
    """
    Get the path to the CSV file
    For backward compatibility, but now returns cached path or Dropbox URL

    Returns:
        str: Path to CSV file or URL
    """
    # Check if cached file exists
    if CACHE_FILE.exists():
        return str(CACHE_FILE)

    # Otherwise return Dropbox URL
    return DROPBOX_CSV_URL


def load_csv_data() -> pd.DataFrame:
    """
    Load the pi-t20.csv data from Dropbox

    Returns:
        pandas DataFrame with the CSV data
    """
    return load_csv_from_dropbox()
