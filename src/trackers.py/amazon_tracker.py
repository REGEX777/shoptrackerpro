import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

header = os.getenv('HEADER')
url = "https://www.amazon.in/Apple-iPhone-Pro-Max-256/dp/B0CHX68YG9/ref=sr_1_3?sr=8-3"

headers = {
    "User-Agent": header
}

def get_price():
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    price_element = soup.select_one("span#priceblock_ourprice")

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

if __name__ == "__main__":
    track_price()
