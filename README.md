# T20 Pressure Index Application

A comprehensive real-time pressure quantification tool for T20 cricket run chases, implementing the methodology from the research paper:

> **"Applications of higher order Markov models and Pressure Index to strategize controlled run chases in Twenty20 cricket"**
> 
> *Authors: Rhitankar Bandyopadhyay (Indian Statistical Institute, Kolkata) & Dibyojyoti Bhattacharjee (Assam University, Silchar)*

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)


## Live App

The application will open in your default browser at `https://t20-pressure-index.streamlit.app`

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


