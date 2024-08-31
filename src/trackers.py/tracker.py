import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import os
import logging
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# select user agent from environment variable or use a default value
user_agent = os.getenv('HEADER', "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
headers = {"User-Agent": user_agent}

# configure logging with detailed formatting
logging.basicConfig(filename='price_tracker.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize mongoDB client and database
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["price_tracker"]
collection = db["product_prices"]

# get the links from the file
def read_urls_from_file(file_path='links.txt'):
    """Read URLs from the specified file path."""
    urls = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            urls = [line.strip() for line in file if line.strip()]
    return urls

# retrieve the price and name from the web pages 
def get_price_and_name(url):
    """Fetch the product name and price from the given URL."""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        if "flipkart.com" in url:
            price_selector = "div._30jeq3._16Jk6d"
            name_selector = "span.B_NuCI"
        elif "amazon.in" in url:
            price_selector = "span.a-price-whole"
            fraction_selector = "span.a-price-fraction"
            name_selector = "span#productTitle"
        else:
            return None, None

        price_element = soup.select_one(price_selector)
        fraction_element = soup.select_one(fraction_selector) if "amazon.in" in url else None
        product_name_element = soup.select_one(name_selector)

        price = (price_element.text.strip() + (fraction_element.text.strip() if fraction_element else "")) if price_element else None
        name = product_name_element.text.strip() if product_name_element else None

        return name, price
    except requests.RequestException as e:
        logging.error(f"Error fetching data from {url}: {e}")
        return None, None

# this function will format the price and add the currency symbol
def format_price(price):
    """Format the price string to a float."""
    return float(price.replace("₹", "").replace(",", "")) if price else None

# save the scrapped product name and price in xlsx
def save_to_excel(data, file_path='price_tracker.xlsx'):
    """Save data to an Excel file, appending if the file already exists."""
    df = pd.DataFrame(data)
    try:
        with pd.ExcelWriter(file_path, mode='a' if os.path.exists(file_path) else 'w', engine='openpyxl', if_sheet_exists='overlay' if os.path.exists(file_path) else None) as writer:
            df.to_excel(writer, sheet_name='Prices', index=False, header=not os.path.exists(file_path))
    except PermissionError as e:
        logging.error(f"Permission error: {e}. Ensure the file is not open or locked.")
    except Exception as e:
        logging.error(f"An error occurred while saving to Excel: {e}")

# save the scrapped product name and price in csv format
def save_to_csv(data, file_path='price_tracker.csv'):
    """Save data to a CSV file, appending if the file already exists."""
    df = pd.DataFrame(data)
    df.to_csv(file_path, mode='a' if os.path.exists(file_path) else 'w', header=not os.path.exists(file_path), index=False)

# Save the scrapped product name and price to mongodb
def save_to_mongodb(product_name, price):
    """Save the product name and price to MongoDB."""
    data = {"timestamp": datetime.now(), "product_name": product_name, "price": price}
    collection.insert_one(data)

# Function that will track the prices using the links in the file
def track_prices():
    """Track and log prices from URLs listed in the file."""
    urls = read_urls_from_file()
    data = []
    for url in urls:
        name, price = get_price_and_name(url)
        if price and name:
            formatted_price = format_price(price)
            logging.info(f"Current price of {name} is: ₹{formatted_price}")
            save_to_mongodb(name, formatted_price)
            data.append({"Timestamp": datetime.now(), "Product": name, "Price": f"₹{formatted_price}"})
        else:
            logging.warning(f"Failed to retrieve data for {url}.")
    
    if data:
        save_to_excel(data)
        save_to_csv(data)

if __name__ == "__main__":
    # this will ensure that url are used to track the prices properlu
    track_prices()
