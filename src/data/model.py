class PriceHistory:
    def __init__(self, db):
        self.collection = db.get_collection("price_history")

    def insert_price(self, product_name, price, timestamp):
        self.collection.insert_one({
            "product_name": product_name,
            "price": price,
            "timestamp": timestamp
        })

    def get_price_history(self, product_name):
        return list(self.collection.find({"product_name": product_name}))
