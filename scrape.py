import requests
from bs4 import BeautifulSoup
import sqlite3

# URL stránky s údajmi
url = "https://okte.sk/sk/edc/zverejnovanie-udajov/aktivovana-agregovana-flexibilita-a-zdielanie-elektriny/#date=2025-06-01&page=1"

# Stiahnutie obsahu stránky
response = requests.get(url)
if response.status_code != 200:
    print(f"Chyba pri sťahovaní stránky: {response.status_code}")
    exit()

# Parsovanie HTML obsahu
soup = BeautifulSoup(response.text, 'html.parser')

# Nájdeme tabuľku – predpokladáme, že je to prvá tabuľka na stránke
table = soup.find('table')
# if not table:
#     print("Tabuľka nebola nájdená na stránke.")
#     exit()

# print("\nDebug - Table structure:")
# print(table.prettify()[:500])  # Print first 500 chars of table structure

# Získanie hlavičky tabuľky z prvého riadku
headers = []
first_row = table.find('tr')
if first_row:
    headers = [th.get_text(strip=True) for th in first_row.find_all('th')]
    print("\nHlavička tabuľky:")
    print(" | ".join(headers))
    print("-" * 80)

# Získanie údajov z tabuľky (preskočíme prvý riadok s hlavičkou)
rows = []
all_rows = table.find_all('tr')
print(f"\nDebug - Total rows found: {len(all_rows)}")

for tr in all_rows[1:]:  # Skip header row
    cells = [td.get_text(strip=True) for td in tr.find_all('td')]
    print(f"Debug - Processing row: {cells}")  # Debug print
    
    if len(cells) >= 4:  # Ensure we have all required columns
        try:
            # Format the output with proper number formatting
            period = cells[0]
            flex_kladna = float(cells[1].replace(',', '.'))
            flex_zaporna = float(cells[2].replace(',', '.'))
            elektrina = float(cells[3].replace(',', '.'))
            
            # Print each row as it's processed
            print(f"{period} | {flex_kladna:>10.3f} | {flex_zaporna:>10.3f} | {elektrina:>10.3f}")
            
            # Store the original string values for database
            rows.append(cells)
        except ValueError as e:
            print(f"Chyba pri spracovaní riadku: {cells}")
            print(f"Chybová správa: {e}")
            continue

if not rows:
    print("Neboli nájdené žiadne údaje na spracovanie.")
    exit()

# Pripojenie k SQLite databáze (vytvorí súbor, ak neexistuje)
conn = sqlite3.connect('okte_data.db')
cursor = conn.cursor()

# Vytvorenie tabuľky v databáze
# Sanitize header names for SQL
sanitized_headers = [f'"{header.replace(" ", "_").replace("-", "_")}"' for header in headers]
columns = ', '.join([f'{header} TEXT' for header in sanitized_headers])
create_table_query = f'CREATE TABLE IF NOT EXISTS okte_data ({columns})'
cursor.execute(create_table_query)

# Vloženie údajov do tabuľky
placeholders = ', '.join(['?'] * len(headers))
insert_query = f'INSERT INTO okte_data VALUES ({placeholders})'
cursor.executemany(insert_query, rows)

# Uloženie zmien a zatvorenie spojenia
conn.commit()
conn.close()

print(f"\nÚdaje boli úspešne stiahnuté a uložené do databázy SQLite. Celkový počet záznamov: {len(rows)}")
