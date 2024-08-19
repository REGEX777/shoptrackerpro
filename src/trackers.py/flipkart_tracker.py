import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import os
import logging

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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

logging.basicConfig(filename='price_tracker.log', level=logging.INFO)

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
        return f"₹{price.replace(',', '')}"
    return "Price not found"

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

def track_prices():
    data = []
    for product in products:
        price = get_price(product['url'])
        formatted_price = format_price(price)
        if price:
            logging.info(f"[{datetime.now()}] The current price of {product['name']} is: {formatted_price}")
            data.append({
                "Timestamp": datetime.now(),
                "Product": product['name'],
                "Price": formatted_price
            })
        else:
            logging.warning(f"[{datetime.now()}] Failed to retrieve the price for {product['name']}.")
    
    if data:
        save_to_excel(data, "price_tracker.xlsx")
        save_to_csv(data, "price_tracker.csv")

if __name__ == "__main__":
    track_prices()
