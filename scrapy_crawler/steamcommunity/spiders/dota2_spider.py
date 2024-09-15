import scrapy
import re
from datetime import datetime


class Dota2Spider(scrapy.Spider):
    name = 'dota2'
    start_urls = ['https://steamcommunity.com/market/search/render/?query=&start=0&count=10&search_descriptions=0&sort_column=popular&sort_dir=desc&appid=570&norender=1']

    def parse(self, response):
        meta = {'proxy': 'http://scraperapi:5b6943bfd05794a7d66dd6cc2468e372@proxy-server.scraperapi.com:8001'}
        json_response = response.json()
        # check if it is first page
        if '&start=0' in response.url:
            # get total count of items
            total_count = json_response['total_count']
            # get all items, looping through pages
            for i in range(1, total_count, 100):
                next_page_url = response.url.replace('&start=0', f'&start={i}')
                yield scrapy.Request(next_page_url, callback=self.parse, meta={'proxy': 'http://scraperapi:5b6943bfd05794a7d66dd6cc2468e372@proxy-server.scraperapi.com:8001'})
        # get items details
        for item in json_response['results']:
            item_details_url = f'https://steamcommunity.com/market/listings/570/{item.get("name")}'
            yield scrapy.Request(item_details_url, callback=self.parse_details_page, meta={'item': item, 'proxy': 'http://scraperapi:5b6943bfd05794a7d66dd6cc2468e372@proxy-server.scraperapi.com:8001'})

    def parse_details_page(self, response):
        item = response.meta['item']
        id_pattern = r'Market_LoadOrderSpread\(\s*(\d+)\s*\)'
        id = re.findall(id_pattern, response.text)
        if id:
            item['id'] = id[0]
            yield scrapy.Request(f'https://steamcommunity.com/market/itemordershistogram?country=UAE&language=english&currency=1&item_nameid={id[0]}&norender=1', callback=self.parse_order_histogram, meta={'item': item})

    def parse_order_histogram(self, response):
        item = response.meta['item']
        json_response = response.json()
        item['order_histogram'] = json_response
        item['scraping_timestampe'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        yield item
