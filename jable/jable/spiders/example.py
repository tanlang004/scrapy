import scrapy
from scrapy.http import Response
import re
from jable.items import JableItem
base_url = "https://missavt.com/sort/month_hot/"


class ExampleSpider(scrapy.Spider):
    name = "jable"
    # allowed_domains = ["example.com"]
    start_urls = [base_url]

    def parse(self, response: Response):
        # print(response.text)
        txt = response.text
        data = response.xpath('//*[@class="video-item"]/a/div[1]/@data-url').getall()
        print(data)
        print(len(data))
        data = [data[0]]
        for detail in data:
            item = JableItem()
            item['url'] = detail
            yield item

    