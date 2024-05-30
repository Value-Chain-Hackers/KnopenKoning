import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Import your spider class
from supplycrawler.supplycrawler.spiders.unilever import UnileverBrandsSpider

# Optional: Configure logging
logging.basicConfig(
    filename='scrapy_log.txt',
    format='%(levelname)s: %(message)s',
    level=logging.INFO
)

# Optional: Custom settings
custom_settings = {
    'ITEM_PIPELINES': {
       "supplycrawler.supplycrawler.pipelines.SupplycrawlerPipeline": 300,
    },
    'FEEDS': {
        'data/Unilever/crawler_output.json': {
            'format': 'json',
            'encoding': 'utf8',
            'store_empty': False,
            'indent': 4,
        },
    },
}

# Create a process with the project's settings
process = CrawlerProcess({**get_project_settings(), **custom_settings})

# Add your spider to the process
process.crawl(UnileverBrandsSpider)

# Start the crawling process
result = process.start()
print(result)