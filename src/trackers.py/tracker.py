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
    {"url": "https://www.flipkart.com/apple-2020-macbook-air-m1-8-gb-256-gb-ssd-mac-os-big-sur-mgn63hn-a/p/itm3c872f9e67bc6?pid=COMFXEKMGNHZYFH9&lid=LSTCOMFXEKMGNHZYFH9P56X45&marketplace=FLIPKART&q=macbook&store=6bo%2Fb5g&spotlightTagId=FkPickId_6bo%2Fb5g&srno=s_1_1&otracker=AS_QueryStore_OrganicAutoSuggest_1_4_na_na_na&otracker1=AS_QueryStore_OrganicAutoSuggest_1_4_na_na_na&fm=search-autosuggest&iid=56f39a35-2ac0-4144-a515-ef9ccc459847.COMFXEKMGNHZYFH9.SEARCH&ppt=sp&ppn=sp&ssid=ckk78prmhc0000001725048487419&qH=864faee128623e2f", "source": "flipkart"},
    {"url": "https://www.amazon.in/2022-Apple-MacBook-Laptop-chip/dp/B0B3BMKMGP/", "source": "amazon"},
]

headers = {"User-Agent": header}

logging.basicConfig(filename='price_tracker.log', level=logging.INFO)

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["price_tracker"]
collection = db["product_prices"]

def get_urls_from_user():
    urls = []
    print("enter product URLs (type 'done' when finished):")
    while True:
        url = input("enter URL: ").strip()
        if url.lower() == 'done':
            break
        urls.append(url)
    
    with open('links.txt', 'w') as file:
        for url in urls:
            file.write(f"{url}\n")

def read_urls_from_file():
    urls = []
    if os.path.exists('links.txt'):
        with open('links.txt', 'r') as file:
            urls = [line.strip() for line in file if line.strip()]
    return urls

def get_price_and_name(product):
    url = product['url']
    source = product['source']
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        if source == "flipkart":
            price_element = soup.select_one("div._30jeq3._16Jk6d") # div name
            product_name_element = soup.select_one("span.B_NuCI")
            price = price_element.text.strip() if price_element else None
            name = product_name_element.text.strip() if product_name_element else None
        elif source == "amazon":
            price_element = soup.select_one("span.a-price-whole") # ele,ent selector amazon
            fraction_element = soup.select_one("span.a-price-fraction")
            product_name_element = soup.select_one("span#productTitle")
            if price_element:
                price = price_element.text.strip() + (fraction_element.text.strip() if fraction_element else "")
            else:
                price = None
            name = product_name_element.text.strip() if product_name_element else None
        return name, price
    except requests.RequestException as e:
        logging.error(f"Error fetching the data from {url}: {e}")
        return None, None

def format_price(price):
    return float(price.replace("₹", "").replace(",", "")) if price else None

# save to excel
def save_to_excel(data, file_path):
    df = pd.DataFrame(data)
    mode = 'a' if os.path.exists(file_path) else 'w'
    
    try:
        if mode == 'a':
            with pd.ExcelWriter(file_path, mode=mode, if_sheet_exists='overlay') as writer:
                df.to_excel(writer, sheet_name='Prices', index=False, header=False)
        else:
            with pd.ExcelWriter(file_path, mode=mode) as writer:
                df.to_excel(writer, sheet_name='Prices', index=False, header=False)
    except PermissionError as e:
        logging.error(f"Permission error: {e}. Make sure the file is not open or locked.")
    except Exception as e:
        logging.error(f"An error occurred while saving to Excel: {e}")

# save the data in csv
def save_to_csv(data, file_path):
    df = pd.DataFrame(data)
    df.to_csv(file_path, mode='a' if os.path.exists(file_path) else 'w', header=False, index=False)


# DATABASE LELELELELE
def save_to_mongodb(product_name, price):
    data = {"timestamp": datetime.now(), "product_name": product_name, "price": price}
    collection.insert_one(data)


# log the current prices in the log file presnet in root
def track_prices():
    data = []
    for product in products:
        name, price = get_price_and_name(product)
        if price and name:
            formatted_price = format_price(price)
            logging.info(f"[{datetime.now()}] the current price of {name} is: ₹{formatted_price}")
            save_to_mongodb(name, formatted_price)
            data.append({"Timestamp": datetime.now(), "Product": name, "Price": f"₹{formatted_price}"})
        else:
            logging.warning(f"[{datetime.now()}] failed to retrieve the data for {product['url']}.")
    
    if data:
        save_to_excel(data, "price_tracker.xlsx")
        save_to_csv(data, "price_tracker.csv")

if __name__ == "__main__":
    track_prices()
