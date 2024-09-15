# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo
from config import config


class SteamcommunityPipeline:

    def __init__(self) -> None:
        parameters = config("mongodb")
        mongodb_uri = parameters.get("uri")
        client = pymongo.MongoClient(mongodb_uri)
        db = client["steamcommunity"]
        self.collection = db["dota2"]

    def get_mongodb_connection(self):
        parameters = config("mongodb")
        mongodb_uri = parameters.get("uri")
        self.client = pymongo.MongoClient(mongodb_uri)
        db = self.client["steamcommunity"]
        return db["dota2_scrapy"]

    def process_item(self, item, spider):
        item_id = item.get('id')
        item.pop('id', None)
        update_current_results = self.collection.update_one({"_id": item_id}, {"$set": item}, upsert=True)
        spider.logger.info(f"updated {update_current_results.modified_count} item and inserted document with id {update_current_results.upserted_id}")
        return item
