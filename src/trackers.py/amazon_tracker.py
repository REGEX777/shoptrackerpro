import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import os
import pandas as pd
import time

load_dotenv()

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["price_tracker"]
products_collection = db["products"]
prices_collection = db["amazon_prices"]

header = os.getenv('HEADER')

headers = {
    "User-Agent": header
}

def get_price(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    price_element = soup.select_one("span#priceblock_ourprice")
    return price_element.text.strip() if price_element else None

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

def track_prices():
    products = list(products_collection.find())
    price_data = []
    for product in products:
        price = get_price(product['url'])
        if price:
            current_price = float(price.replace('₹', '').replace(',', ''))
            last_entry = prices_collection.find_one({"product": product['name']}, sort=[("timestamp", -1)])
            if last_entry and current_price < float(last_entry['price'].replace('₹', '').replace(',', '')):
                print(f"[{datetime.now()}] Price drop detected for {product['name']}. New price: {price}")
                save_to_mongodb(product['name'], price)
                price_data.append({
                    "Timestamp": datetime.now(),
                    "Product": product['name'],
                    "Price": price
                })
            else:
                print(f"[{datetime.now()}] No price drop for {product['name']}. Current price: {price}")
                save_to_mongodb(product['name'], price)
                price_data.append({
                    "Timestamp": datetime.now(),
                    "Product": product['name'],
                    "Price": price
                })
    save_to_excel(price_data, "price_tracker.xlsx")

if __name__ == "__main__":
    while True:
        track_prices()
        time.sleep(3600)
