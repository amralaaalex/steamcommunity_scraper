# Steam Community Scraper

This project contains two web crawlers designed to scrape data from the Steam Community website. The crawlers are implemented using two different frameworks: Scrapy and Selenium. Below is a detailed description of each crawler and the differences between them.

## Scrapy is More Convenient for This Website and for Your Entire Project
The task asked for the use of Selenium or any other browser-based solution to access dynamic content. However, for this website, the dynamic content can be parsed by accessing the hidden backend APIs of the site. Therefore, there is no need to use a browser-based scraper here.

here's an example of hidden API's used for this scraper
try to access this URL, please
[Steam Market Item Orders Histogram](https://steamcommunity.com/market/itemordershistogram?country=EG&language=english&currency=1&item_nameid=176454825&norender=1)

that's what the scrapy crawler is parsing, sweet right?!

In general, browser-based scrapers should be the last resort as they come with many disadvantages, especially for large-scale scraping systems. If you're scraping millions of URLs daily, Scrapy is definitely the better choice.

Browser-based scrapers consume a lot of memory and CPU, are not consistent, are hard to scale, and difficult to use for concurrency. We should only rely on browser-based scrapers if all other HTTP request scrapers fail.

Based on my 8+ years of experience scraping over 8,000 websites, true dynamic content on blog/article websites that cannot be parsed using pure HTTP requests is rare. Usually, accessing the hidden APIs of a website is enough to parse dynamic content.

Another advantage of accessing dynamic content from hidden APIs is that it often provides more data. Not all data entries are displayed on the rendered page, and the structured data from APIs is extremely valuable for machine learning training.


Nonetheless, I have created two dockerized solutions here: one that uses Scrapy and another that uses Selenium. Both solutions push the scraped data to a MongoDB database, but each stores the data in separate collections.

## website anti-bot status analysis

the website is hosted on a `nginx` server, and its only anti-bot tool implemented is to block fast huge requests fromt he same IP. chaning user-agents values have no effect on it from the same IP.

**result**: basic data center proxy with rotation IP's can parse the content of this website with no issue.

## improvements
here's a list of points that should be implemented in case it goes to production:
1) proxy credentials.
2) scraping inputs to limit the scraper scope, like scraping specific items only, or to scrape only data from search pages not detailes pages

## Scrapy Crawler

### Usage
change directory to `scrapy_crawler`
`cd scrapy_crawler`
build it 
`docker build -t scrapy-crawler .`
run it 
`docker run -d --name scrapy_crawler scrapy-crawler`
check the logs
`docker logs -f scrapy_crawler`


## Selenium Crawler

### Usage
change directory to `selenium_crawler`
build it 
`docker build -t selenium-crawler .`
run it 
`docker run -d --name selenium_crawler selenium-crawler`
check the logs
`docker logs -f selenium_crawler`

## Check the Scraped Data
you can find a file `parameters.ini`, it has URI to access the db and see the data, you can just paste it to mongoDB Compass application. 
