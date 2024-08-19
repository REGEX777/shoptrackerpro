import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

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

def track_price():
    price = get_price()
    if price:
        print(f"[{datetime.now()}] The current price of the product is: {price}")
    else:
        print(f"[{datetime.now()}] Failed to retrieve the price.")

if __name__ == "__mai