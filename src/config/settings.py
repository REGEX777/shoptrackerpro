import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    return {
        "mongo_uri": os.getenv("MONGO_URI"),
        "db_name": os.getenv("DB_NAME", "price_tracker"),
        "scrape_interval": int(os.getenv("SCRAPE_INTERVAL", 3600)),
        "notification_email": os.getenv("NOTIFICATION_EMAIL")
    }
