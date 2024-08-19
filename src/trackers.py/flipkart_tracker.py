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
collection = db["flipkart_prices"]



header = os.getenv('HEADER')
url = "https://www.flipkart.com/apple-iphone-14-pro-space-black-128-gb/p/itm5e220e9a699fb"

headers = {
    "User-Agent": header
}

def get_price():
    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.content, "html.parser")

    price_element = soup.select_one("div._30jeq3._16Jk6d")

    if price_element:
        return price_element.text.strip()
    else:
        return None

def save_to_mongodb(price):
    data = {
        "timestamp": datetime.now(),
        "price": price
    }
    collection.insert_one(data)

def save_to_excel(price, file_path):
    # lets make a dataframeeeeeee
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
        print(f"[{datetime.now()}] The current price of the product is: {price}")
    else:
        print(f"[{datetime.now()}] Failed to retrieve the price.")

if __name__ == "__mai