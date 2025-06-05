# OKTE Data Scraper

This script scrapes data from the OKTE website (https://okte.sk) and stores it in a SQLite database.

## Requirements

- Python 3.7+
- Required packages (install using `pip install -r requirements.txt`):
  - requests
  - beautifulsoup4
  - pandas

## Usage

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Run the script:
```bash
python scrape_okte.py
```

The script will:
- Create a SQLite database file named `okte_data.db`
- Scrape the data from the OKTE website
- Store the data in the database
- Display the first 5 records from the database

## Database Schema

The data is stored in a table named `flexibilita_data` with the following columns:
- id (INTEGER, PRIMARY KEY)
- datum (DATE)
- zuctovacia_perioda (TEXT)
- aktivovana_agregovana_flexibilita_kladna (REAL)
- aktivovana_agregovana_flexibilita_zaporna (REAL)
- zdielana_elektrina (REAL) 