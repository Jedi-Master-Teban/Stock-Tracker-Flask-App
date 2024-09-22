# app.py
from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import yfinance as yf
import os

app = Flask(__name__)

# Path to the CSV file
CSV_FILE_PATH = 'transactions.csv'

# Initialize DataFrame to store transactions
if os.path.exists(CSV_FILE_PATH):
    transactions = pd.read_csv(CSV_FILE_PATH)
else:
    transactions = pd.DataFrame(columns=['Date', 'Type', 'Symbol', 'Quantity', 'Price', 'Cash'])

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html', transactions=transactions.to_html())

# Route to add a transaction
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    global transactions
    date = request.form['date']
    type_ = request.form['type']
    symbol = request.form['symbol']
    quantity = float(request.form['quantity'])
    price = float(request.form['price'])
    cash = float(request.form['cash'])
    
    new_transaction = pd.DataFrame([[date, type_, symbol, quantity, price, cash]], 
                                   columns=['Date', 'Type', 'Symbol', 'Quantity', 'Price', 'Cash'])
    transactions = pd.concat([transactions, new_transaction], ignore_index=True)
    
    # Save the updated DataFrame to the CSV file
    transactions.to_csv(CSV_FILE_PATH, index=False)
    
    return redirect(url_for('home'))

# Function to get current stock price
def get_stock_price(symbol):
    stock = yf.Ticker(symbol)
    return stock.history(period='1d')['Close'][0]

# Function to calculate P/L and P/L%
def calculate_pl():
    global transactions
    pl = 0
    for index, row in transactions.iterrows():
        if row['Type'] == 'buy':
            current_price = get_stock_price(row['Symbol'])
            pl += (current_price - row['Price']) * row['Quantity']
    return pl

# Route for the dashboard
@app.route('/dashboard')
def dashboard():
    pl = calculate_pl()
    return render_template('dashboard.html', pl=pl, transactions=transactions.to_html())

if __name__ == '__main__':
    app.run(debug=True)