# T20 Pressure Index Application

Pressure Index (PI) is a ball-by-ball metric designed to quantify the pressure experienced by a team while batting second in a limited-overs cricket match. Based on the foundation laid by H.H Lemmer and Dibyojyoti Bhattacharjee (2016) and several subsequent extended works over the years, the current study by Rhitankar Bandyopadhyay and Dibyojyoti Bhattacharjee (2025), in their research paper 'Applications of higher order Markov models and Pressure Index to strategize controlled run chases in Twenty20 cricket', focuses on phasewise third order Markov models and Gamma distribution fallbacks to strategize controlled run chases in T20 cricket.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)


## Live App

Use the app here: `https://t20-pressure-index.streamlit.app`

## Project Structure

```
pressure-index/
├── main.py                         # Main file
├── requirements.txt                # Dependencies
├── README.md                       # This file
├── data/
│   ├── duckworth_lewis_table.csv   # D/L resource table
│   └── pdf file                    # Research paper
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


