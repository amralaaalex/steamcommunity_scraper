from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import time
import pymongo
from config import config
import re
import json


class SteamScraper:
    def __init__(self, mongo_uri, mongo_db, mongo_collection):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.driver = self.initialize_driver()
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection = self.db[self.mongo_collection]

    def initialize_driver(self):
        print("initializing the driver")
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run Chrome in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=service, options=options)
        print("driver initialized")
        return driver

    def access_searchpage(self, url):
        time.sleep(2)
        counter = 0
        while counter < 3:
            self.driver.get(url)
            time.sleep(1)
            if 'There was an error getting listings for this item. Please try again later.' in self.driver.page_source:
                print(f"failed to access details page, retrying, {counter}")
                time.sleep(1)
                counter += 1
                continue
            try:
                # wait for an item to load using WebDriverWait
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "searchResultsRows"))
                )
                return True
            except Exception as e:
                print("retrying failed request to access search page")
                time.sleep(1)
                counter += 1
                continue
        return False

    def access_detailspage(self, url):
        time.sleep(2)
        counter = 0
        while counter < 3:
            self.driver.get(url)
            time.sleep(1)
            if 'There was an error getting listings for this item. Please try again later.' in self.driver.page_source:
                print(f"failed to access details page, retrying, {counter}")
                time.sleep(1)
                counter += 1
                continue
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "pricehistory"))
                )
                return True
            except Exception as e:
                print("retrying failed request to access details page")
                time.sleep(1)
                counter += 1
                continue
        return False

    def extract_blocks(self):
        blocks = self.driver.find_elements(By.CLASS_NAME, "market_listing_row_link")
        return blocks

    def extract_details_and_urls(self, block):
        item = {}
        item['name'] = block.find_element(By.CLASS_NAME, "market_listing_item_name").text
        item['image_url'] = block.find_element(By.CLASS_NAME, "market_listing_item_img").get_attribute("src")
        item['quantity'] = block.find_element(By.CLASS_NAME, "market_listing_num_listings_qty").text
        item['price'] = block.find_element(By.CSS_SELECTOR, "span.market_table_value.normal_price > span.normal_price").text
        item['url'] = block.get_attribute("href")
        return item

    def get_item_id(self, page_source):
        id_regex = r'Market_LoadOrderSpread\(\s*(\d+)\s*\)'
        id = re.findall(id_regex, page_source)
        if id:
            return id[0]
        else:
            return None

    def get_extra_data(self, page_source):
        extra_data_regex = 'var g_rgAssets = ([^\n]*)'
        try:
            extra_data = re.search(extra_data_regex, page_source).group(1)
            return json.loads(extra_data[:-1])
        except AttributeError:
            return None

    def get_activity_history(self, page_source):
        activity_history_regex = 'var line1=([^;]*)'
        try:
            activity_history = re.search(activity_history_regex, page_source).group(1)
            return json.loads(activity_history)
        except AttributeError:
            return None

    def get_more_data(self, url):
        success = self.access_detailspage(url)
        if not success:
            print("failed to access details page")
            return {}
        details_dict = {}
        # get source code as string
        page_source = self.driver.page_source
        id = self.get_item_id(page_source)
        if id:
            details_dict['id'] = id
        else:
            return details_dict
        details_dict['description'] = self.driver.find_element(By.CLASS_NAME, "item_desc_descriptors").text
        details_dict['extra_data'] = self.get_extra_data(page_source)
        details_dict['activity_history'] = self.get_activity_history(page_source)
        return details_dict

    def scrape(self, start_url):
        pages_counter = 0
        print("accessing the first page")
        success = self.access_searchpage(start_url)
        if not success:
            print("failed to access first page")
            return
        while True:
            time.sleep(2)
            pages_counter += 1
            print(f"scraping page #{pages_counter}")
            current_serachpage_url = self.driver.current_url
            blocks = self.extract_blocks()
            print(f"there are {len(blocks)} items in this page")
            items_list = [self.extract_details_and_urls(block) for block in blocks]

            bulk_operations = []
            for item in items_list:
                time.sleep(1)
                print("getting details for item", item.get('name'))
                more_data = self.get_more_data(item.get('url'))
                item.update(more_data)
                item_id = item.get('id')
                item.pop('id', None)
                item['scraping_timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
                bulk_operations.append(
                    pymongo.UpdateOne({"_id": item_id}, {"$set": item}, upsert=True)
                )

            if bulk_operations:
                print(f"updating the database with {len(bulk_operations)} items")
                result = self.collection.bulk_write(bulk_operations, ordered=False)
                print(f"Matched {result.matched_count} documents, Modified {result.modified_count} documents, Upserted {result.upserted_count} documents")

            print("getting back to the search page")
            # make sure to visit the search page again not an item details page
            success = self.access_searchpage(current_serachpage_url)
            if not success:
                print("failed to access search page")
                break
            # check if there is a next button
            next_button = self.driver.find_element(By.ID, "searchResults_btn_next")
            if next_button:
                # get class name of this button
                next_button_class = next_button.get_attribute("class")
                if "disabled" in next_button_class:
                    print("no more pages")
                    break
                else:
                    print("clicking next button")
                    next_button.click()
                    time.sleep(2)
            else:
                print("no more pages")
                break

    def close(self):
        self.driver.quit()
        self.client.close()


if __name__ == "__main__":
    parameters = config("mongodb")
    mongo_uri = parameters.get("uri")
    mongo_db = "steamcommunity"
    mongo_collection = "dota2_selenium"
    start_url = "https://steamcommunity.com/market/search?appid=570"

    scraper = SteamScraper(mongo_uri, mongo_db, mongo_collection)
    scraper.scrape(start_url)
    scraper.close()
