# Deployment Guide - Streamlit Cloud

## Overview
This guide explains how to deploy the Pressure Index app to Streamlit Cloud with the large CSV file hosted on Dropbox.

## Data Configuration

### Large CSV File on Dropbox
The `pi-t20.csv` file (176.3 MB) is hosted on Dropbox instead of GitHub due to file size limitations.

**Dropbox Link**: https://www.dropbox.com/scl/fi/ngtum2qeh8q727dlwfpxj/pi-t20.csv?rlkey=vjt63fwe4jzb6ewvilorl0252&st=12ydinys&dl=0

**Direct Download Link** (used by the app):
https://www.dropbox.com/scl/fi/ngtum2qeh8q727dlwfpxj/pi-t20.csv?rlkey=vjt63fwe4jzb6ewvilorl0252&st=12ydinys&dl=1

### How It Works

1. **CSV Loader Module** (`src/utils/csv_loader.py`):
   - Loads the CSV directly from Dropbox
   - Caches the data using `@st.cache_data` for 24 hours
   - Optionally stores a local cache at `~/.cache/pressure_index/pi-t20.csv`

2. **Modified Files**:
   - `src/pages/clutch_players.py` - Loads from Dropbox
   - `src/pages/clutch_teams.py` - Loads from Dropbox
   - `src/pages/past_matches.py` - Loads from Dropbox
   - `src/utils/data_handler.py` - Accepts DataFrame directly

## GitHub Repository Setup

### Step 1: Create GitHub Repository

```bash
cd /Users/rhitankarsmacbook/Downloads/pressure-index

# Initialize git (if not already done)
git init

# Add all files EXCEPT pi-t20.csv (already removed from data folder)
git add .

# Commit
git commit -m "Initial commit - Pressure Index App"

# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/pressure-index.git

# Push to GitHub
git push -u origin main
```

### Step 2: .gitignore Configuration

Ensure your `.gitignore` includes:

```
# Large data files (hosted on Dropbox)
data/pi-t20.csv

# Cache directories
.cache/
__pycache__/
*.pyc

# OS files
.DS_Store
```

## Streamlit Cloud Deployment

### Step 1: Sign Up / Log In
1. Go to https://share.streamlit.io/
2. Sign in with your GitHub account

### Step 2: Deploy New App
1. Click "New app"
2. Select your repository: `YOUR_USERNAME/pressure-index`
3. Set branch: `main`
4. Set main file path: `main.py`
5. Click "Deploy"

### Step 3: Wait for Deployment
- Streamlit Cloud will install dependencies from `requirements.txt`
- First load will download the CSV from Dropbox (takes ~30-60 seconds)
- Subsequent loads will be fast due to caching

## Performance Optimization

### Caching Strategy

The app uses Streamlit's caching to minimize data loading:

```python
@st.cache_data(ttl=86400)  # 24 hour cache
def load_csv_from_dropbox(url):
    df = pd.read_csv(url)
    return df
```

### First Load
- Downloads 176.3 MB CSV from Dropbox
- Takes ~30-60 seconds depending on connection
- Shows loading spinner: "Loading dataset from Dropbox..."

### Subsequent Loads
- Uses cached DataFrame
- Near-instant loading
- Cache persists for 24 hours

## Updating the Dropbox Link

If you need to change the Dropbox link in the future:

1. Edit `src/utils/csv_loader.py`
2. Update the `DROPBOX_CSV_URL` variable:

```python
DROPBOX_CSV_URL = "https://www.dropbox.com/scl/fi/YOUR_NEW_LINK?dl=1"
```

**Important**: Always ensure the link ends with `dl=1` (direct download) instead of `dl=0`.

## Local Testing

To test the app locally with the Dropbox link:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run main.py
```

On first run, it will download the CSV from Dropbox and cache it locally.

## Files Structure

```
pressure-index/
├── main.py                          # Main app entry point
├── requirements.txt                 # Python dependencies
├── data/
│   ├── duckworth_lewis_table.csv   # Small file (in GitHub)
│   └── Applications_of_higher_order_Markov_models_...pdf  # Research paper
├── src/
│   ├── utils/
│   │   ├── csv_loader.py           # NEW: Dropbox CSV loader
│   │   ├── data_handler.py         # Updated to accept DataFrame
│   │   ├── cricinfo_scraper.py
│   │   ├── pressure_index.py
│   │   └── visualizations.py
│   ├── pages/
│   │   ├── live_tracker.py
│   │   ├── past_matches.py         # Updated for Dropbox
│   │   ├── clutch_players.py       # Updated for Dropbox
│   │   ├── clutch_teams.py         # Updated for Dropbox
│   │   └── how_it_works.py
│   └── components/
│       └── ui_components.py
└── .gitignore
```

## Troubleshooting

### Issue: "Unable to load data from Dropbox"
**Solution**:
- Check that the Dropbox link is valid and accessible
- Ensure the link ends with `dl=1` not `dl=0`
- Verify internet connection

### Issue: Slow loading on first access
**Expected**: The first load downloads 176.3 MB, which takes 30-60 seconds
**Solution**: This is normal. Subsequent loads will be instant due to caching.

### Issue: Cache expired, slow load again
**Expected**: After 24 hours, cache expires and data reloads
**Solution**: This is by design. You can adjust the TTL in `csv_loader.py`:

```python
@st.cache_data(ttl=86400)  # Change to desired seconds
```

## Environment Variables (Optional)

For additional security, you can use Streamlit secrets for the Dropbox URL:

1. In Streamlit Cloud, go to app settings → Secrets
2. Add:

```toml
[dropbox]
csv_url = "https://www.dropbox.com/scl/fi/ngtum2qeh8q727dlwfpxj/pi-t20.csv?rlkey=vjt63fwe4jzb6ewvilorl0252&st=12ydinys&dl=1"
```

3. Update `csv_loader.py`:

```python
import streamlit as st

# Try to get from secrets, fallback to hardcoded
try:
    DROPBOX_CSV_URL = st.secrets["dropbox"]["csv_url"]
except:
    DROPBOX_CSV_URL = "https://www.dropbox.com/scl/fi/..."
```

## Post-Deployment Checklist

- [ ] App loads without errors
- [ ] All sections work: Live Tracker, Past Matches, Clutch Players, Clutch Teams, How It Works
- [ ] PDF displays correctly in "How It Works"
- [ ] Data loads from Dropbox successfully
- [ ] Caching works (second page load is fast)
- [ ] Live match tracking works
- [ ] Ball-by-ball commentary fetching works

## Support

For issues or questions:
- Check Streamlit Cloud logs
- Verify Dropbox link accessibility
- Ensure all dependencies are in `requirements.txt`

## App URL

Once deployed, your app will be available at:
```
https://YOUR_USERNAME-pressure-index-main-HASH.streamlit.app
```

Or with a custom URL if you set one up in Streamlit Cloud settings.
