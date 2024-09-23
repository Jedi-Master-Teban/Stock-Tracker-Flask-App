from flask import Flask, request, render_template, redirect, url_for, flash
import pandas as pd
import yfinance as yf
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flashing messages

# Path to the CSV file
CSV_FILE_PATH = 'transactions.csv'

# Initialize DataFrame to store transactions
if os.path.exists(CSV_FILE_PATH):
    transactions = pd.read_csv(CSV_FILE_PATH)
else:
    transactions = pd.DataFrame(columns=['Date', 'Type', 'Symbol', 'Quantity', 'Price', 'Cash'])

# Function to get current stock price
def get_stock_price(symbol):
    stock = yf.Ticker(symbol)
    return stock.history(period='1d')['Close'][0]

# Function to calculate portfolio value
def calculate_portfolio_value():
    global transactions
    portfolio_value = 0
    cash_balance = 0
    for index, row in transactions.iterrows():
        if row['Type'] == 'buy':
            current_price = get_stock_price(row['Symbol'])
            portfolio_value += current_price * row['Quantity']
        elif row['Type'] == 'deposit':
            cash_balance += row['Cash']
    return round(portfolio_value + cash_balance, 3)

def calculate_portfolio_composition():
    composition = transactions.groupby('Symbol').agg({
        'Quantity': 'sum',
        'Price': 'mean'
    }).reset_index()
    composition['Total Value'] = composition['Quantity'] * composition['Price']
    return composition

# Function to get current prices and P/L of all assets
def get_current_prices_and_pl():
    global transactions
    current_prices = {}
    pl_values = {}
    for symbol in transactions['Symbol'].unique():
        if pd.notna(symbol):  # Skip NaN values for deposits
            symbol = symbol.upper()
            current_price = round(get_stock_price(symbol), 3)
            total_quantity = transactions[transactions['Symbol'] == symbol]['Quantity'].sum()
            total_cost = (transactions[transactions['Symbol'] == symbol]['Quantity'] * transactions[transactions['Symbol'] == symbol]['Price']).sum()
            pl = round((current_price * total_quantity) - total_cost, 3)
            pl_percent = round((pl / total_cost) * 100, 3) if total_cost != 0 else 0
            current_prices[symbol] = current_price
            pl_values[symbol] = (pl, pl_percent)
    return current_prices, pl_values

# Route for the home page
@app.route('/')
def home():
    portfolio_value = calculate_portfolio_value()
    current_prices, pl_values = get_current_prices_and_pl()
    return render_template('index.html', transactions=transactions, portfolio_value=portfolio_value, current_prices=current_prices, pl_values=pl_values)

# Route for the transactions page
@app.route('/transactions')
def transactions_page():
    return render_template('transactions.html', transactions=transactions)

# Route to add a transaction
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    global transactions
    date = request.form['date']
    type_ = request.form['type']
    symbol = request.form['symbol'].upper() if type_ != 'deposit' else None
    quantity = float(request.form['quantity']) if type_ != 'deposit' else None
    price = float(request.form['price']) if type_ != 'deposit' else None
    cash = float(request.form['cash']) if type_ == 'deposit' else 0
    
    # Server-side validation for cash amount
    if type_ == 'deposit' and cash <= 0:
        flash("Cash amount must be a positive number.")
        return redirect(url_for('home'))
    
    new_transaction = pd.DataFrame([[date, type_, symbol, quantity, price, cash]], 
                                   columns=['Date', 'Type', 'Symbol', 'Quantity', 'Price', 'Cash'])
    transactions = pd.concat([transactions, new_transaction], ignore_index=True)
    
    # Save the updated DataFrame to the CSV file
    transactions.to_csv(CSV_FILE_PATH, index=False)
    
    return redirect(url_for('home'))

@app.route('/portfolio_composition')
def portfolio_composition():
    composition = calculate_portfolio_composition()
    return render_template('portfolio_composition.html', composition=composition)


if __name__ == '__main__':
    app.run(debug=True)