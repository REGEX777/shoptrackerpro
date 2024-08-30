import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import os
import logging
from pymongo import MongoClient

load_dotenv()

header = os.getenv('HEADER') or "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
products = [
    {"name": "iPhone 14 Pro", "url": "https://www.flipkart.com/apple-iphone-14-pro-space-black-128-gb/p/itm5e220e9a699fb", "threshold": 120000},
    {"name": "Canon R100 Mirrorless Camera", "url": "https://www.flipkart.com/canon-r100-mirrorless-camera-rf-s-18-45mm-f-4-5-6-3-stm/p/itm3bc65ea11d81b", "threshold": 50000},
]

headers = {"User-Agent": header}

logging.basicConfig(filename='price_tracker.log', level=logging.INFO)

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["price_tracker"]
collection = db["product_prices"]
daily_collection = db["daily_prices"]

def get_price(url):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        price_element = soup.select_one("div._30jeq3._16Jk6d")
        return price_element.text.strip() if price_element else None
    except requests.RequestException as e:
        logging.error(f"Error fetching the price from {url}: {e}")
        return None

def format_price(price):
    return float(price.replace("₹", "").replace(",", "")) if price else None

def save_to_excel(data, file_path):
    df = pd.DataFrame(data)
    with pd.ExcelWriter(file_path, mode='a' if os.path.exists(file_path) else 'w', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, sheet_name='Prices', index=False, header=False)

def save_to_csv(data, file_path):
    df = pd.DataFrame(data)
    df.to_csv(file_path, mode='a' if os.path.exists(file_path) else 'w', header=False, index=False)

def save_to_mongodb(product_name, price):
    data = {"timestamp": datetime.now(), "product_name": product_name, "price": price}
    collection.insert_one(data)

def save_daily_prices():
    for product in products:
        daily_data = list(collection.find({
            "product_name": product['name'],
            "timestamp": {"$gte": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)}
        }))
        if daily_data:
            daily_collection.insert_many(daily_data)

def get_lowest_price(product_name):
    record = collection.find({"product_name": product_name}).sort("price", 1).limit(1)
    return record[0]['price'] if record.count() > 0 else None

def calculate_price_change_rate(product_name):
    historical_data = list(collection.find({"product_name": product_name}).sort("timestamp", 1))
    if len(historical_data) < 2:
        logging.warning(f"Not enough data to calculate price change rate for {product_name}.")
        return None
    first_price, last_price = historical_data[0]['price'], historical_data[-1]['price']
    time_difference = (historical_data[-1]['timestamp'] - historical_data[0]['timestamp']).total_seconds() / 3600
    return (last_price - first_price) / time_difference if time_difference else None

def alert_price_drop(product_name, price, threshold):
    if price < threshold:
        logging.info(f"[{datetime.now()}] ALERT: {product_name} price dropped to ₹{price}, which is below the threshold of ₹{threshold}.")
        print(f"ALERT: {product_name} price dropped to ₹{price}. Below threshold!")

def analyze_price_trends(product_name):
    historical_data = list(collection.find({"product_name": product_name}))
    if not historical_data:
        logging.warning(f"No data available to analyze for {product_name}.")
        return
    prices = [record['price'] for record in historical_data]
    lowest_price, highest_price, latest_price = min(prices), max(prices), prices[-1]
    price_change_rate = calculate_price_change_rate(product_name)
    print(f"Analysis for {product_name}:")
    print(f"Lowest Price: ₹{lowest_price}")
    print(f"Highest Price: ₹{highest_price}")
    print(f"Latest Recorded Price: ₹{latest_price}")
    print(f"Price Change Rate: ₹{price_change_rate:.2f} per hour" if price_change_rate is not None else "Not enough data to calculate price change rate.")

def track_prices():
    data = []
    for product in products:
        price = get_price(product['url'])
        if price:
            formatted_price = format_price(price)
            logging.info(f"[{datetime.now()}] The current price of {product['name']} is: ₹{formatted_price}")
            save_to_mongodb(product['name'], formatted_price)
            save_daily_prices()
            lowest_price = get_lowest_price(product['name'])
            if lowest_price and formatted_price < lowest_price:
                logging.info(f"New lowest price for {product['name']}: ₹{formatted_price}")
                alert_price_drop(product['name'], formatted_price, product['threshold'])
            data.append({"Timestamp": datetime.now(), "Product": product['name'], "Price": f"₹{formatted_price}"})
        else:
            logging.warning(f"[{datetime.now()}] Failed to retrieve the price for {product['name']}.")
    
    if data:
        save_to_excel(data, "price_tracker.xlsx")
        save_to_csv(data, "price_tracker.csv")

if __name__ == "__main__":
    track_prices()
    for product in products:
        analyze_price_trends(product["name"])
