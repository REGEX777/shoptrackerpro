import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import os
import logging
from pymongo import MongoClient

load_dotenv()

header = os.getenv('HEADER')

products = [
    {
        "name": "iPhone 14 Pro",
        "url": "https://www.flipkart.com/apple-iphone-14-pro-space-black-128-gb/p/itm5e220e9a699fb"
    },
    {
        "name": "Canon R100 Mirrorless Camera RF-S 18-45mm f/4.5-6.3 IS STM",
        "url": "https://www.flipkart.com/canon-r100-mirrorless-camera-rf-s-18-45mm-f-4-5-6-3-stm/p/itm3bc65ea11d81b"
    },
]

headers = {
    "User-Agent": header or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

logging.basicConfig(filename='price_tracker.log', level=logging.INFO)

# mongodb setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["price_tracker"]
collection = db["product_prices"]

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
    if price:
        return float(price.replace("₹", "").replace(",", ""))
    return None

def save_to_excel(data, file_path):
    df = pd.DataFrame(data)
    if os.path.exists(file_path):
        with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='overlay') as writer:
            df.to_excel(writer, sheet_name='Prices', index=False, header=False)
    else:
        with pd.ExcelWriter(file_path) as writer:
            df.to_excel(writer, sheet_name='Prices', index=False)

def save_to_csv(data, file_path):
    df = pd.DataFrame(data)
    if os.path.exists(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(file_path, index=False)

def save_to_mongodb(product_name, price):
    data = {
        "timestamp": datetime.now(),
        "product_name": product_name,
        "price": price
    }
    collection.insert_one(data)

def get_lowest_price(product_name):
    record = collection.find({"product_name": product_name}).sort("price", 1).limit(1)
    return record[0]['price'] if record.count() > 0 else None

def analyze_price_trends(product_name):
    historical_data = list(collection.find({"product_name": product_name}))
    
    if not historical_data:
        logging.warning(f"No data available to analyze for {product_name}.")
        return
    
    prices = [record['price'] for record in historical_data]
    lowest_price = min(prices)
    highest_price = max(prices)
    latest_price = prices[-1]
    
    print(f"Analysis for {product_name}:")
    print(f"Lowest Price: ₹{lowest_price}")
    print(f"Highest Price: ₹{highest_price}")
    print(f"Latest Recorded Price: ₹{latest_price}")

def track_prices():
    data = []
    for product in products:
        price = get_price(product['url'])
        if price:
            formatted_price = format_price(price)
            logging.info(f"[{datetime.now()}] The current price of {product['name']} is: ₹{formatted_price}")
            save_to_mongodb(product['name'], formatted_price)
            lowest_price = get_lowest_price(product['name'])
            if lowest_price and formatted_price < lowest_price:
                logging.info(f"New lowest price for {product['name']}: ₹{formatted_price}")
            data.append({
                "Timestamp": datetime.now(),
                "Product": product['name'],
                "Price": f"₹{formatted_price}"
            })
        else:
            logging.warning(f"[{datetime.now()}] Failed to retrieve the price for {product['name']}.")
    
    if data:
        save_to_excel(data, "price_tracker.xlsx")
        save_to_csv(data, "price_tracker.csv")

if __name__ == "__main__":
    track_prices()
    for product in products:
        analyze_price_trends(product["name"])
