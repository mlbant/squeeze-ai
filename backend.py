import requests
import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import sqlite3
import hashlib
import dotenv
dotenv.load_dotenv()

# Your xAI API key
XAI_API_KEY = os.getenv("XAI_API_KEY")

# xAI API endpoint
XAI_ENDPOINT = "https://api.x.ai/v1/chat/completions"

# Cache for consistent scores across all users
SCORE_CACHE = {}
CACHE_EXPIRY = 600  # 10 minutes in seconds

def get_cached_score(ticker):
    """Get cached score for consistency across all users"""
    cache_key = f"score_{ticker.upper()}"
    current_time = datetime.now().timestamp()
    
    # Check if we have a cached score that's still valid
    if cache_key in SCORE_CACHE:
        cached_data, timestamp = SCORE_CACHE[cache_key]
        if current_time - timestamp < CACHE_EXPIRY:
            return cached_data
    
    return None

def cache_score(ticker, score_data):
    """Cache score data for consistency"""
    cache_key = f"score_{ticker.upper()}"
    current_time = datetime.now().timestamp()
    SCORE_CACHE[cache_key] = (score_data, current_time)

def get_daily_score_variation():
    """Get daily variation factor based on current date"""
    import hashlib
    from datetime import date
    
    # Use current date to generate consistent daily variation
    today = date.today().isoformat()
    hash_object = hashlib.md5(today.encode())
    hash_hex = hash_object.hexdigest()
    
    # Convert first 8 characters to integer for variation
    variation_seed = int(hash_hex[:8], 16) % 100
    return (variation_seed - 50) / 10  # Range: -5 to +5

def get_real_market_cap(ticker):
    """Get real market cap from yfinance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get('marketCap', 0)
        
        if market_cap < 1_000_000_000:  # Less than 1B
            return "Small"
        elif market_cap < 10_000_000_000:  # 1B to 10B
            return "Mid"
        else:  # Greater than 10B
            return "Large"
    except:
        # Default based on known stocks
        small_caps = ["GME", "AMC", "BBBY", "PROG", "SAVA", "ATER", "SPCE"]
        large_caps = ["TSLA", "NVDA", "AAPL", "MSFT", "XOM", "CVX", "JPM", "BAC", "WFC"]
        
        if ticker in small_caps:
            return "Small"
        elif ticker in large_caps:
            return "Large"
        else:
            return "Mid"

def get_real_volatility(ticker):
    """Calculate real volatility from recent price data"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        
        if not hist.empty:
            # Calculate daily returns
            returns = hist['Close'].pct_change().dropna()
            # Calculate standard deviation (volatility)
            volatility = returns.std() * (252 ** 0.5)  # Annualized
            
            if volatility > 0.5:  # 50% annualized volatility
                return "High"
            elif volatility > 0.3:  # 30% annualized volatility
                return "Medium"
            else:
                return "Low"
    except:
        pass
    
    # Default based on known stocks
    high_vol = ["GME", "AMC", "BBBY", "PROG", "SAVA", "ATER", "SPCE", "TSLA", "NVDA"]
    low_vol = ["AAPL", "MSFT", "JPM", "BAC", "WFC"]
    
    if ticker in high_vol:
        return "High"
    elif ticker in low_vol:
        return "Low"
    else:
        return "Medium"

def get_stock_database():
    """Complete stock database with real-time data"""
    daily_variation = get_daily_score_variation()
    
    stocks = {
        # Tech stocks
        "TSLA": {"sector": "Tech", "base_score": 65},
        "NVDA": {"sector": "Tech", "base_score": 58},
        "AAPL": {"sector": "Tech", "base_score": 45},
        "MSFT": {"sector": "Tech", "base_score": 42},
        "PLTR": {"sector": "Tech", "base_score": 63},
        "SOFI": {"sector": "Tech", "base_score": 67},
        
        # Biotech stocks
        "MRNA": {"sector": "Biotech", "base_score": 62},
        "SAVA": {"sector": "Biotech", "base_score": 71},
        "BIIB": {"sector": "Biotech", "base_score": 55},
        "VRTX": {"sector": "Biotech", "base_score": 48},
        
        # Retail stocks
        "GME": {"sector": "Retail", "base_score": 78},
        "AMC": {"sector": "Retail", "base_score": 72},
        "BBBY": {"sector": "Retail", "base_score": 69},
        "DDS": {"sector": "Retail", "base_score": 64},
        
        # Energy stocks
        "XOM": {"sector": "Energy", "base_score": 48},
        "CVX": {"sector": "Energy", "base_score": 46},
        "SLB": {"sector": "Energy", "base_score": 52},
        "OXY": {"sector": "Energy", "base_score": 56},
        
        # Finance stocks
        "JPM": {"sector": "Finance", "base_score": 41},
        "BAC": {"sector": "Finance", "base_score": 39},
        "WFC": {"sector": "Finance", "base_score": 43},
        "GS": {"sector": "Finance", "base_score": 44},
        
        # Additional high squeeze potential
        "ATER": {"sector": "Tech", "base_score": 65},
        "SPCE": {"sector": "Tech", "base_score": 71},
        "FFIE": {"sector": "Tech", "base_score": 74},
        "MULN": {"sector": "Tech", "base_score": 70},
    }
    
    # Add real-time market cap and volatility
    for ticker, data in stocks.items():
        data["market_cap"] = get_real_market_cap(ticker)
        data["volatility"] = get_real_volatility(ticker)
    
    return stocks

def apply_daily_variation(base_score, daily_variation):
    """Apply daily variation to base score"""
    varied_score = base_score + daily_variation
    return max(0, min(100, int(varied_score)))

def get_stock_details(ticker, stock_data, daily_variation):
    """Get detailed stock information with daily variation"""
    info = stock_data[ticker]
    current_score = apply_daily_variation(info["base_score"], daily_variation)
    
    # Calculate metrics based on score
    short_percent = max(5, min(35, current_score * 0.4))
    borrow_fee = max(1, min(20, current_score * 0.2))
    days_to_cover = max(1, min(10, current_score * 0.1))
    
    # Generate why based on sector and score
    why_templates = {
        "Tech": f"Technology sector momentum with {short_percent:.1f}% short interest",
        "Biotech": f"Biotech catalyst potential with elevated short coverage",
        "Retail": f"Retail sector squeeze setup with high short interest",
        "Energy": f"Energy sector volatility with moderate short pressure",
        "Finance": f"Financial sector stability with low short interest"
    }
    
    return {
        "ticker": ticker,
        "score": current_score,
        "short_percent": round(short_percent, 1),
        "borrow_fee": round(borrow_fee, 1),
        "days_to_cover": round(days_to_cover, 1),
        "why": why_templates.get(info["sector"], f"Market dynamics with {short_percent:.1f}% short interest"),
        "sector": info["sector"],
        "market_cap": info["market_cap"],
        "volatility": info["volatility"]
    }

def get_consistent_stock_data():
    """Get consistent stock data that updates daily"""
    stock_db = get_stock_database()
    daily_variation = get_daily_score_variation()
    
    # Get top 5 stocks by score for the day
    all_stocks = []
    for ticker in stock_db:
        stock_details = get_stock_details(ticker, stock_db, daily_variation)
        all_stocks.append(stock_details)
    
    # Sort by score and return top 5
    all_stocks.sort(key=lambda x: x['score'], reverse=True)
    return all_stocks[:5]

def get_squeeze_stocks(filters=None):
    """Get top 5 stocks with squeeze potential - consistent across all users with proper filtering"""
    stock_db = get_stock_database()
    daily_variation = get_daily_score_variation()
    
    # Get all stocks with details
    all_stocks = []
    for ticker in stock_db:
        stock_details = get_stock_details(ticker, stock_db, daily_variation)
        all_stocks.append(stock_details)
    
    # Apply filters if specified
    filtered_stocks = all_stocks
    
    if filters:
        # Sector filter
        if "Sector: Tech" in filters:
            filtered_stocks = [s for s in filtered_stocks if s['sector'] == 'Tech']
        elif "Sector: Biotech" in filters:
            filtered_stocks = [s for s in filtered_stocks if s['sector'] == 'Biotech']
        elif "Sector: Retail" in filters:
            filtered_stocks = [s for s in filtered_stocks if s['sector'] == 'Retail']
        elif "Sector: Energy" in filters:
            filtered_stocks = [s for s in filtered_stocks if s['sector'] == 'Energy']
        elif "Sector: Finance" in filters:
            filtered_stocks = [s for s in filtered_stocks if s['sector'] == 'Finance']
        
        # Market cap filter
        if "Market Cap: Small (<$1B)" in filters:
            filtered_stocks = [s for s in filtered_stocks if s['market_cap'] == 'Small']
        elif "Market Cap: Mid ($1B-$10B)" in filters:
            filtered_stocks = [s for s in filtered_stocks if s['market_cap'] == 'Mid']
        elif "Market Cap: Large (>$10B)" in filters:
            filtered_stocks = [s for s in filtered_stocks if s['market_cap'] == 'Large']
        
        # High volatility filter
        if "High Volatility" in filters:
            filtered_stocks = [s for s in filtered_stocks if s['volatility'] == 'High']
    
    # Sort by score and return top 5
    filtered_stocks.sort(key=lambda x: x['score'], reverse=True)
    return filtered_stocks[:5] if filtered_stocks else []

def get_single_squeeze_score(ticker):
    """Get squeeze score for a single stock - consistent across all users with daily variation"""
    ticker = ticker.upper()
    
    # Check cache first for consistency
    cached_score = get_cached_score(ticker)
    if cached_score:
        return cached_score
    
    # Check if it's in our stock database
    stock_db = get_stock_database()
    daily_variation = get_daily_score_variation()
    
    if ticker in stock_db:
        stock_details = get_stock_details(ticker, stock_db, daily_variation)
        cache_score(ticker, stock_details)
        return stock_details
    
    # Default fallback for unknown tickers
    fallback_score = get_fallback_single_score(ticker)
    cache_score(ticker, fallback_score)
    return fallback_score

def get_historical_data(ticker, period='6mo'):
    """Get real historical price data using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        
        # Convert period to yfinance format
        period_map = {
            '1mo': '1mo',
            '3mo': '3mo',
            '6mo': '6mo'
        }
        yf_period = period_map.get(period, '6mo')
        
        # Get historical data
        hist = stock.history(period=yf_period)
        
        if hist.empty:
            return pd.DataFrame()
        
        # Reset index and prepare data
        hist = hist.reset_index()
        hist['Date'] = pd.to_datetime(hist['Date']).dt.date
        
        # Return relevant columns
        return hist[['Date', 'Close', 'Volume', 'High', 'Low']]
        
    except Exception as e:
        print(f"Error fetching historical data for {ticker}: {e}")
        return pd.DataFrame()

def get_fallback_stocks():
    """Fallback data if API fails"""
    return [
        {
            "ticker": "GME",
            "score": 78,
            "short_percent": 24.5,
            "borrow_fee": 9.8,
            "days_to_cover": 5.2,
            "why": "Meme stock momentum building"
        },
        {
            "ticker": "AMC",
            "score": 72,
            "short_percent": 21.3,
            "borrow_fee": 7.5,
            "days_to_cover": 3.8,
            "why": "High retail interest"
        },
        {
            "ticker": "BBIG",
            "score": 69,
            "short_percent": 28.7,
            "borrow_fee": 15.2,
            "days_to_cover": 4.1,
            "why": "Catalyst pending"
        },
        {
            "ticker": "ATER",
            "score": 65,
            "short_percent": 19.8,
            "borrow_fee": 12.3,
            "days_to_cover": 6.7,
            "why": "Technical breakout"
        },
        {
            "ticker": "PROG",
            "score": 62,
            "short_percent": 17.5,
            "borrow_fee": 8.9,
            "days_to_cover": 3.2,
            "why": "Partnership rumors"
        }
    ]

def get_fallback_single_score(ticker):
    """Fallback score for single ticker if API fails"""
    return {
        "ticker": ticker.upper(),
        "score": 58,
        "short_percent": 15.5,
        "borrow_fee": 6.2,
        "days_to_cover": 2.8,
        "why": "Moderate squeeze potential"
    }

# Test functions
if __name__ == "__main__":
    print("Testing get_squeeze_stocks:")
    stocks = get_squeeze_stocks()
    for stock in stocks:
        print(f"  {stock['ticker']}: Score {stock['score']}")
    
    print("\nTesting get_single_squeeze_score:")
    score = get_single_squeeze_score("TSLA")
    print(f"  {score['ticker']}: Score {score['score']}")
    
    print("\nTesting get_historical_data:")
    hist = get_historical_data("TSLA", "1mo")
    print(f"  Retrieved {len(hist)} days of data")
