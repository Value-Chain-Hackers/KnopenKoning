import scrapy

class MySpider(scrapy.Spider):
    name = 'unileverscrapy'
    start_urls = ['https://www.unilever.com']

    def parse(self, response):
        # Example: Extracting titles and links
        for item in response.css('article'):
            yield {
                'title': item.css('h3::text').get(),
                'link': item.css('a::attr(href)').get(),
            }
       
