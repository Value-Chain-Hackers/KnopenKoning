import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Import your spider class
from supplycrawler.supplycrawler.spiders.unilever_brands import UnileverBrandsSpider

# Optional: Configure logging
logging.basicConfig(
    filename='scrapy_log.txt',
    format='%(levelname)s: %(message)s',
    level=logging.INFO
)

# Optional: Custom settings
custom_settings = {
    'LOG_LEVEL': 'DEBUG',
    'ITEM_PIPELINES': {
        'myproject.pipelines.MyPipeline': 300,
    }
}

# Create a process with the project's settings
process = CrawlerProcess({**get_project_settings(), **custom_settings})

# Add your spider to the process
process.crawl(ExampleSpider)

# Start the crawling process
process.start()
