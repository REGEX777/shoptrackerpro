import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import os
import pandas as pd
import time
from collections import defaultdict
import logging

load_dotenv()

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["price_tracker"]
products_collection = db["products"]
prices_collection = db["amazon_prices"]

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

def save_to_excel(price_data, file_path):
    df = pd.DataFrame(price_data)
    if os.path.exists(file_path):
        with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='overlay') as writer:
            df.to_excel(writer, sheet_name='Prices', index=False, header=False)
    else:
        with pd.ExcelWriter(file_path) as writer:
            df.to_excel(writer, sheet_name='Prices', index=False)

def aggregate_price_data():
    pipeline = [
        {
            "$group": {
                "_id": "$product",
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"},
                "average_price": {"$avg": "$price"},
                "last_checked": {"$max": "$timestamp"}
            }
        }
    ]
    return list(prices_collection.aggregate(pipeline))

def generate_report():
    aggregated_data = aggregate_price_data()
    report_data = []
    for data in aggregated_data:
        report_data.append({
            "Product": data["_id"],
            "Min Price": data["min_price"],
            "Max Price": data["max_price"],
            "Average Price": data["average_price"],
            "Last Checked": data["last_checked"]
        })
    df = pd.DataFrame(report_data)
    report_path = f"price_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(report_path, index=False)
    logging.info(f"Generated report: {report_path}")

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
            else:
                save_to_mongodb(product['name'], price)
                price_data.append({
                    "Timestamp": datetime.now(),
                    "Product": product['name'],
                    "Price": price
                })
        else:
            logging.warning(f"Failed to retrieve price for {product['name']}")
    save_to_excel(price_data, "price_tracker.xlsx")
    logging.info(f"Tracked prices for {len(products)} products")

if __name__ == "__main__":
    try:
        while True:
            track_prices()
            if datetime.now().hour == 0:  # Generate a report at midnight
                generate_report()
            time.sleep(3600)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise
