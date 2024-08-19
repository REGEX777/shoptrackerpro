import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
import os
import pandas as pd
import time
import logging

load_dotenv()

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["price_tracker"]
products_collection = db["products"]
prices_collection = db["amazon_prices"]
price_drops_collection = db["price_drops"]

header = os.getenv('HEADER')

headers = {
    "User-Agent": header
}

logging.basicConfig(filename='tracker.log', level=logging.INFO)

def get_price(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        price_element = soup.select_one("span#priceblock_ourprice")
        return price_element.text.strip() if price_element else None
    except Exception as e:
        logging.error(f"Error fetching price from {url}: {str(e)}")
        return None

def save_to_mongodb(product_name, price):
    data = {
        "timestamp": datetime.now(),
        "product": product_name,
        "price": price
    }
    prices_collection.insert_one(data)

def save_to_csv(price_data, file_path):
    df = pd.DataFrame(price_data)
    if os.path.exists(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(file_path, index=False)

def log_price_drop(product_name, old_price, new_price):
    data = {
        "timestamp": datetime.now(),
        "product": product_name,
        "old_price": old_price,
        "new_price": new_price,
        "price_drop": old_price - new_price
    }
    price_drops_collection.insert_one(data)

def calculate_price_change(product_name):
    recent_prices = list(prices_collection.find({"product": product_name}).sort("timestamp", -1).limit(2))
    if len(recent_prices) == 2:
        old_price = float(recent_prices[1]["price"].replace('₹', '').replace(',', ''))
        new_price = float(recent_prices[0]["price"].replace('₹', '').replace(',', ''))
        if new_price < old_price:
            log_price_drop(product_name, old_price, new_price)
        return round(((new_price - old_price) / old_price) * 100, 2)
    return None

def generate_trend_analysis():
    products = list(prices_collection.distinct("product"))
    trend_data = []
    for product in products:
        product_prices = list(prices_collection.find({"product": product}))
        if len(product_prices) > 1:
            timestamps = [entry["timestamp"] for entry in product_prices]
            prices = [float(entry["price"].replace('₹', '').replace(',', '')) for entry in product_prices]
            trend_data.append({
                "Product": product,
                "First Tracked": timestamps[0],
                "Last Tracked": timestamps[-1],
                "Price Change (%)": round(((prices[-1] - prices[0]) / prices[0]) * 100, 2)
            })
    df = pd.DataFrame(trend_data)
    trend_report_path = f"price_trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(trend_report_path, index=False)
    logging.info(f"Generated trend analysis: {trend_report_path}")

def track_prices():
    products = list(products_collection.find())
    price_data = []
    for product in products:
        price = get_price(product['url'])
        if price:
            current_price = float(price.replace('₹', '').replace(',', ''))
            last_entry = prices_collection.find_one({"product": product['name']}, sort=[("timestamp", -1)])
            if last_entry and current_price < float(last_entry['price'].replace('₹', '').replace(',', '')):
                save_to_mongodb(product['name'], price)
                price_data.append({
                    "Timestamp": datetime.now(),
                    "Product": product['name'],
                    "Price": price
                })
                calculate_price_change(product['name'])
            else:
                save_to_mongodb(product['name'], price)
                price_data.append({
                    "Timestamp": datetime.now(),
                    "Product": product['name'],
                    "Price": price
                })
        else:
            logging.warning(f"Failed to retrieve price for {product['name']}")
    save_to_csv(price_data, "price_tracker.csv")
    logging.info(f"Tracked prices for {len(products)} products")

if __name__ == "__main__":
    try:
        while True:
            track_prices()
            if datetime.now().hour == 0:  
                generate_trend_analysis()
            time.sleep(3600)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise
