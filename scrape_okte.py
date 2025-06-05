import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

def create_database():
    """Create SQLite database and table for storing the data."""
    conn = sqlite3.connect('okte_data.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS okte_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datum TEXT,
        zuctovacia_perioda TEXT,
        aktivovana_agregovana_flexibilita_kladna REAL,
        aktivovana_agregovana_flexibilita_zaporna REAL,
        zdielana_elektrina REAL
    )
    ''')
    
    conn.commit()
    return conn

def parse_number(text):
    """Parse number from text, handling negative numbers and non-breaking spaces."""
    # Remove non-breaking spaces and regular spaces
    text = text.strip().replace('\xa0', '').replace(' ', '')
    # Handle negative numbers
    if text.startswith('-'):
        return -float(text[1:].replace(',', '.'))
    return float(text.replace(',', '.'))

def scrape_data_for_date(date_str):
    """Scrape data for a specific date."""
    base_url = "https://okte.sk/sk/edc/zverejnovanie-udajov/aktivovana-agregovana-flexibilita-a-zdielanie-elektriny/"
    url = f"{base_url}#date={date_str}&page=1"
    
    try:
        print(f"Setting up Chrome driver for {date_str}...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        print(f"Fetching data for {date_str}...")
        driver.get(url)
        
        # Wait for the data table to load
        print("Waiting for data table to load...")
        wait = WebDriverWait(driver, 10)
        table = wait.until(EC.presence_of_element_located((By.ID, "exportableTable2")))
        
        # Give a little extra time for data to load
        time.sleep(2)
        
        # Get the page source after JavaScript has loaded the content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the specific table by ID
        data_table = soup.find('table', id='exportableTable2')
        if not data_table:
            print("Data table not found")
            driver.quit()
            return None
        
        print("Data table found, extracting data...")
        
        # Get data rows
        data = []
        tbody = data_table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            print(f"Found {len(rows)} data rows")
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    try:
                        period = cols[0].text.strip()
                        flex_kladna = parse_number(cols[1].text)
                        flex_zaporna = parse_number(cols[2].text)
                        elektrina = parse_number(cols[3].text)
                        
                        data.append({
                            'datum': date_str,
                            'zuctovacia_perioda': period,
                            'aktivovana_agregovana_flexibilita_kladna': flex_kladna,
                            'aktivovana_agregovana_flexibilita_zaporna': flex_zaporna,
                            'zdielana_elektrina': elektrina
                        })
                    except ValueError as e:
                        print(f"Error processing row: {cols}")
                        print(f"Error details: {e}")
                        continue
        
        driver.quit()
        
        if data:
            # Save to database
            conn = create_database()
            cursor = conn.cursor()
            
            for row in data:
                cursor.execute('''
                INSERT INTO okte_data 
                (datum, zuctovacia_perioda, aktivovana_agregovana_flexibilita_kladna, 
                 aktivovana_agregovana_flexibilita_zaporna, zdielana_elektrina)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    row['datum'],
                    row['zuctovacia_perioda'],
                    row['aktivovana_agregovana_flexibilita_kladna'],
                    row['aktivovana_agregovana_flexibilita_zaporna'],
                    row['zdielana_elektrina']
                ))
            
            conn.commit()
            conn.close()
            print(f"Successfully saved {len(data)} records for {date_str}")
        
        return data
    
    except Exception as e:
        print(f"Error scraping data for {date_str}: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

def main():
    """Main function for command-line usage."""
    print("Starting data scraping from OKTE website...")
    
    # Get date from user
    date_str = input("Enter date to scrape (YYYY-MM-DD): ")
    
    # Scrape data
    data = scrape_data_for_date(date_str)
    
    if data:
        # Display the data
        display_data(data)
    else:
        print("No data was scraped")

def display_data(data):
    """Display scraped data in a formatted table."""
    if not data:
        print("No data to display")
        return
    
    # Convert data to list of lists for tabulate
    table_data = []
    for row in data:
        table_data.append([
            row['datum'],
            row['zuctovacia_perioda'],
            f"{row['aktivovana_agregovana_flexibilita_kladna']:>10.3f}",
            f"{row['aktivovana_agregovana_flexibilita_zaporna']:>10.3f}",
            f"{row['zdielana_elektrina']:>10.3f}"
        ])
    
    # Define headers
    headers = [
        'Dátum',
        'Zúčtovacia perióda',
        'Aktivovaná agregovaná flexibilita kladná',
        'Aktivovaná agregovaná flexibilita záporná',
        'Zdieľaná elektrina'
    ]
    
    # Print the table
    print("\nScraped Data:")
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    print(f"\nTotal records: {len(data)}")

if __name__ == "__main__":
    main() 