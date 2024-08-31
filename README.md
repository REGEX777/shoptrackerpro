

Price Tracker
=============

This project is a Python-based price tracker that monitors the prices of products on Amazon and Flipkart. It fetches the prices and logs the data into MongoDB, as well as saving it in Excel and CSV formats.

Installation
------------

To install the required dependencies, run the following command:

    pip install -r requirements.txt

Project Structure
-----------------

*   **db.py:** Contains the MongoDB wrapper class.
*   **model.py:** Contains functions to scrape prices, log data, and save data to MongoDB, Excel, and CSV.
*   **trackers.py:** Contains the main tracking logic, including the instantiation of trackers for Amazon and Flipkart.
*   **main.py:** The main entry point for the application, setting up configuration and scheduling tasks.

How to Use
----------

1.  Configure your MongoDB URI and database name in `db.py`.
2.  Run the application using the following command:

    python main.py

3.  Enter the links to the products and prices will be logged into MongoDB, and data will be saved in Excel and CSV formats.

Environment Variables
---------------------

Create a `.env` file in the root of the project with the following variables:

    HEADER="Your user agent string here"

Logging
-------

The application logs price tracking information and errors in `price_tracker.log`.

Dependencies
------------

*   `pymongo`
*   `requests`
*   `beautifulsoup4`
*   `python-dotenv`
*   `pandas`

License
-------

This project is licensed under the MIT License.
