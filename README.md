# T20 Pressure Index Application

A comprehensive real-time pressure quantification tool for T20 cricket run chases, implementing the methodology from the research paper:

> **"Applications of higher order Markov models and Pressure Index to strategize controlled run chases in Twenty20 cricket"**
> 
> *Authors: Rhitankar Bandyopadhyay (Indian Statistical Institute, Kolkata) & Dibyojyoti Bhattacharjee (Assam University, Silchar)*

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

### 1. Live PI Tracker
- Real-time tracking of live T20 matches from ESPN Cricinfo
- Ball-by-ball Pressure Index calculation during 2nd innings
- Strategic projections for next 1, 2, 3 overs
- Live pressure curve visualization with zone indicators
- Auto-refresh every 30 seconds

### 2. Past Matches Analysis
- **Historical Match Data**: Search and analyze past matches with detailed pressure curves
- **Compare Past Matches**: Overlay two historical matches for comparison
- **Live vs Historical**: Compare ongoing match with historical data in real-time

### 3. How It Works
- Comprehensive explanation of the Pressure Index formula
- Wicket weights and their significance
- Phase-wise analysis (Powerplay, Middle Overs, Death Overs)
- Strategic zone recommendations

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup

1. **Clone or download the repository**
```bash
cd pressure-index
```

2. **Create a virtual environment (recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Dataset (Automatic)**
The large dataset (`pi-t20.csv`, 176.3 MB) is automatically loaded from Dropbox on first run.
No manual download needed! The app will:
- Download the data automatically on first load (~30-60 seconds)
- Cache it for 24 hours for instant subsequent loads
- Show a loading spinner during download

## Running the Application

```bash
streamlit run main.py
```

The application will open in your default browser at `http://localhost:8501`

## Project Structure

```
pressure-index/
├── main.py                 # Main entry point
├── requirements.txt        # Dependencies
├── README.md              # This file
├── data/
│   ├── duckworth_lewis_table.csv   # D/L resource table
│   └── Applications_of_higher_order_Markov_models_...pdf  # Research paper
├── src/
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── csv_loader.py           # Dropbox CSV loader (auto-download)
│   │   ├── pressure_index.py       # PI calculation engine
│   │   ├── cricinfo_scraper.py     # Live data scraping
│   │   ├── data_handler.py         # Dataset processing
│   │   └── visualizations.py       # Chart generation
│   ├── components/
│   │   └── ui_components.py        # UI elements
│   └── pages/
│       ├── live_tracker.py         # Live matches page
│       ├── past_matches.py         # Historical data page
│       └── how_it_works.py         # Documentation page
└── assets/                         # Static assets (icons, images)
```

## The Pressure Index Formula

```
PI = (CRRR/IRRR) × (1/2) × [e^(RU/100) + e^(Σwi/11)]
```

Where:
- **IRRR** = Initial Required Run Rate
- **CRRR** = Current Required Run Rate
- **RU** = Resources Used (from Duckworth-Lewis table)
- **Σwi** = Sum of wicket weights for fallen wickets

## Strategic Zones

| Zone | PI Range | Win Rate | Recommendation |
|------|----------|----------|----------------|
| Target | < 0.5 | ~100% | Excellent position |
| Acceptable | 0.5 - 1.5 | 70-100% | Maintain approach |
| Risky | 1.5 - 3.5 | 20-70% | Need acceleration |
| Avoid | > 3.5 | < 20% | High pressure |

## Deployment to Streamlit Cloud

1. Push your code to GitHub (large CSV excluded automatically via `.gitignore`)
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Deploy with `main.py` as the entry point

The app automatically loads the large `pi-t20.csv` dataset from Dropbox. No manual data upload needed!

**See `DEPLOYMENT_GUIDE.md` for detailed instructions.**

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Citation

If you use this application in your research, please cite:

```bibtex
@article{bandyopadhyay2025pressure,
  title={Applications of higher order Markov models and Pressure Index to strategize controlled run chases in Twenty20 cricket},
  author={Bandyopadhyay, Rhitankar and Bhattacharjee, Dibyojyoti},
  journal={[Journal Name]},
  year={2025}
}
```

## Contact

**Developed by Rhitankar Bandyopadhyay**

- Twitter: [@rhitankar](https://x.com/rhitankar)
- GitHub: [rhitankar8616](https://github.com/rhitankar8616)
- LinkedIn: [Rhitankar Bandyopadhyay](https://www.linkedin.com/in/rhitankar-bandyopadhyay-a2099227b/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Indian Statistical Institute, Kolkata
- Assam University, Silchar
- ESPN Cricinfo for live match data
- Duckworth-Lewis resource tables
