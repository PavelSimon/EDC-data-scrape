from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
from scrape_okte import scrape_data_for_date
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

def get_db_connection():
    conn = sqlite3.connect('okte_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        try:
            # Convert string dates to datetime objects
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Validate date range
            if end < start:
                flash('End date must be after start date', 'error')
                return redirect(url_for('index'))
            
            # Scrape data for each day in the range
            current = start
            total_records = 0
            
            while current <= end:
                date_str = current.strftime('%Y-%m-%d')
                print(f"Scraping data for {date_str}...")
                
                # Scrape data for current date
                data = scrape_data_for_date(date_str)
                if data:
                    total_records += len(data)
                
                # Move to next day
                current += timedelta(days=1)
            
            flash(f'Successfully scraped {total_records} records', 'success')
            return redirect(url_for('index'))
            
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD', 'error')
            return redirect(url_for('index'))
    
    # Get existing data for display
    conn = get_db_connection()
    data = conn.execute('SELECT * FROM okte_data ORDER BY datum DESC, zuctovacia_perioda').fetchall()
    conn.close()
    
    return render_template('index.html', data=data)

@app.route('/clear', methods=['POST'])
def clear_data():
    conn = get_db_connection()
    conn.execute('DELETE FROM okte_data')
    conn.commit()
    conn.close()
    flash('Database cleared successfully', 'success')
    return redirect(url_for('index'))

@app.route('/graph')
def graph():
    conn = get_db_connection()
    
    # Get date filters from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build the query with optional date filtering
    query = 'SELECT * FROM okte_data'
    params = []
    
    if start_date and end_date:
        query += ' WHERE datum BETWEEN ? AND ?'
        params.extend([start_date, end_date])
    elif start_date:
        query += ' WHERE datum >= ?'
        params.append(start_date)
    elif end_date:
        query += ' WHERE datum <= ?'
        params.append(end_date)
    
    query += ' ORDER BY datum, zuctovacia_perioda'
    
    # Execute query with parameters
    data = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    # Prepare data for plotting
    dates = (data['datum'] + ' ' + data['zuctovacia_perioda']).tolist()
    
    graph_data = [
        {
            'x': dates,
            'y': data['aktivovana_agregovana_flexibilita_kladna'].tolist(),
            'type': 'scatter',
            'name': 'Positive Flexibility'
        },
        {
            'x': dates,
            'y': data['aktivovana_agregovana_flexibilita_zaporna'].tolist(),
            'type': 'scatter',
            'name': 'Negative Flexibility'
        },
        {
            'x': dates,
            'y': data['zdielana_elektrina'].tolist(),
            'type': 'scatter',
            'name': 'Shared Electricity'
        }
    ]
    
    return render_template('graph.html', graph_data=json.dumps(graph_data))

if __name__ == '__main__':
    app.run(debug=True) 