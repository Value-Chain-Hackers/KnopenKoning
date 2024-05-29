import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class UnileverSpider(CrawlSpider):
    name = "unilever"
    allowed_domains = ["unilever.com", "unilever.co.uk", "unilevernotices.com"]
    start_urls = ["https://www.unilever.com/brands/all-brands/?pageSize=48"]

    rules = (Rule(LinkExtractor(), callback="parse_item", follow=True),)

    def parse_item(self, response):
        item = {}
        for item in response.css('article'):
            yield {
                'title':    item.css('span.uol-c-link__label::text').get(),
                'link':     item.css('a::attr(href)').get(),
                'link-text':     item.css('a::text').get(),
                'picture':  item.css('img::attr(src)').get(),
            }
        return item
