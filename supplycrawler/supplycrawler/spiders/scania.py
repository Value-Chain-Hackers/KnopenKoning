import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class ScaniaSpider(CrawlSpider):
    name = "scania"
    allowed_domains = ["www.scania.com"]
    disallowed_domains = ["shop.scania.com", "supplier.scania.com", "accessories.scania.com"]
    start_urls = ["https://scania.com"]

    rules = (Rule(LinkExtractor(allow_domains=allowed_domains, deny_domains=disallowed_domains), callback="parse_item", follow=True),)

    def parse_item(self, response):
        # do not process pages under /customer/
        if "/customer/" in response.url:
            return

        item = {}
        # store the url of the page
        item["url"] = response.url
        
        # get meta data
        item["meta"] = {}
        for meta in response.xpath('//meta'):
            name = meta.xpath('@name').get()
            content = meta.xpath('@content').get()
            if name is not None and content is not None:
                item["meta"][name] = content

        item["title"] = response.xpath('//title').get()
        #item["name"] = response.xpath('//div[@id="name"]').get()
        #item["description"] = response.xpath('//div[@id="description"]').get()
        return item


class ScaniaAccesoriesSpider(CrawlSpider):
    name = "scania_accesories"
    allowed_domains = ["accessories.scania.com"]
    disallowed_domains = ["shop.scania.com", "supplier.scania.com"]
    start_urls = ["https://accessories.scania.com/en/catalog/VA6"]

    rules = (Rule(LinkExtractor(allow=("https://accessories.scania.com/en/"), allow_domains=allowed_domains, deny_domains=disallowed_domains), callback="parse_item", follow=True),)

    def parse_item(self, response):
        
        # do not process pages not under /en/
        if not response.url.startswith("https://accessories.scania.com/en/"):
            return
        
        title = response.xpath("//div[@class='product']//h1/a/text()").get()
        description = response.xpath("//p[@class='product__description']//font/text()").get()
        part_container = response.xpath("//*[@class='teaser__articule']").get()
        if part_container is not None:
            partnr = part_container.split("\n")[1].split(">")[2].strip()
        else:
            partnr = None

        if title is not None and description is not None and partnr is not None:
            yield {
                'title': title,
                'part_nr': partnr,
                'description': description,
                'product_url': response.url
            }

