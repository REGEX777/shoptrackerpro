from src.config.settings import load_config
from src.trackers.amazon_tracker import AmazonTracker
from src.trackers.flipkart_tracker import FlipkartTracker
from src.tasks.scheduler import schedule_tasks

def main():
    config = load_config()
    amazon_tracker = AmazonTracker(config)
    flipkart_tracker = FlipkartTracker(config)
    schedule_tasks([amazon_tracker, flipkart_tracker])

if __name__ == "__main__":
    main()
