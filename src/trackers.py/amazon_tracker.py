import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import os
import pandas as pd

load_dotenv()

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["price_tracker"]
collection = db["amazon_prices"]

header = os.getenv('HEADER')
url = "https://www.amazon.in/Apple-iPhone-Pro-Max-256/dp/B0CHX68YG9/ref=sr_1_3?sr=8-3"

headers = {
    "User-Agent": header
}

def get_price():
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    price_element = soup.select_one("span#priceblock_ourprice")
    return price_element.text.strip() if price_element else None

def format_price(price):
    return price.strip() if price else "Price not found"

def save_to_mongodb(price):
    data = {
        "timestamp": datetime.now(),
        "price": price
    }
    collection.insert_one(data)

def save_to_excel(price, file_path):
    data = {
        "Timestamp": [datetime.now()],
        "Product": ["iPhone 14 Pro"],
        "Price": [format_price(price)]
    }
    df = pd.DataFrame(data)

    if os.path.exists(file_path):
        with pd.ExcelWriter(file_path, mode='a', if_sheet_exists='overlay') as writer:
            df.to_excel(writer, sheet_name='Prices', index=False, header=False)
    else:
        with pd.ExcelWriter(file_path) as writer:
            df.to_excel(writer, sheet_name='Prices', index=False)

def track_price():
    price = get_price()
    if price:
        formatted_price = format_price(price)
        print(f"[{datetime.now()}] The current price of the product is: {formatted_price}")
        save_to_mongodb(formatted_price)
        save_to_excel(formatted_price, "price_tracker.xlsx")
    else:
        print(f"[{datetime.now()}] Failed to retrieve the price.")

if __name__ == "__main__":
    track_price()
