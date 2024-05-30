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



class UnileverBrandsSpider(CrawlSpider):
    name = "unilever_brands"
    allowed_domains = ["unilever.com"]
    start_urls = ["https://www.unilever.com/brands/all-brands/?pageSize=48"]

    rules = (Rule(LinkExtractor("/brands"), callback="parse_item", follow=True),)
    brands = set()
    skiping = ["/brands/innovation"]

    def parse_item(self, response):
        for item in response.css('article'):
            link = item.css('a::attr(href)').get()
            if link is not None and link.startswith('/brands/'):
                if not any(skip in link for skip in self.skiping):
                    if link not in self.brands:
                        self.brands.add(link)
                        if "/brands/whats-in-our-products" not in link:
                            yield {
                                'type': 'brand',
                                'title':         item.css('span.uol-c-link__label::text').get(),
                                'link':          "https://www.unilever.com" + item.css('a::attr(href)').get(),
                                'link-text':     item.css('a::text').get(),
                                'picture':       "https://www.unilever.com" + item.css('img::attr(src)').get(),
                            }
                        else:
                            yield {
                                'type': 'whats-in-our-products',
                                'title':         item.css('span.uol-c-link__label::text').get(),
                                'link':          "https://www.unilever.com" + item.css('a::attr(href)').get(),
                                'link-text':     item.css('a::text').get(),
                                'picture':       "https://www.unilever.com" +  item.css('img::attr(src)').get(),
                            }
