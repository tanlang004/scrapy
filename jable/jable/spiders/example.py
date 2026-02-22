import scrapy
from scrapy.http import Response
import re
from jable.items import JableItem
base_url = "https://jable.tv/hot/?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=video_viewed&from="


class ExampleSpider(scrapy.Spider):
    name = "jable"
    # allowed_domains = ["example.com"]
    start_urls = [f"{base_url}{i}" for i in range(1, 2)]

    def parse(self, response: Response):
        # print(response.text)
        txt = response.text
        data = response.xpath('//*[@class="img-box cover-md"]//a/@href').getall()
        print(data)
        print(len(data))
        data = [data[0]]
        for detail in data:
            yield scrapy.Request(detail, self.detailParse)

    def detailParse(self, response: Response):
        # print(response.url)
        txt = response.text
                # 调整后的正则：捕获hlsUrl变量里的完整URL（从https到.m3u8结尾）
        pattern = r"var hlsUrl\s*=\s*'([^']+\.m3u8)'"

        # 执行匹配
        match = re.search(pattern, txt)

        if match:
            # group(1) 是完整的hlsUrl值（包含整个URL）
            full_hls_url = match.group(1)
            # 可选：如果还需要单独提取文件名，再从完整URL里拆
            
            print(f"✅ 提取到完整的hlsUrl：{full_hls_url}")
            item = JableItem()
            item['url'] = full_hls_url
            yield item
        else:
            print("❌ 未找到hlsUrl变量中的完整.m3u8 URL")