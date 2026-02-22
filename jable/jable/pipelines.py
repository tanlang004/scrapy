# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import asyncio
import time
from pathlib import Path

DOWNLODS_PATH = Path.home().absolute()

class JablePipeline:
    async def process_item(self, item, spider):
        url = item["url"]
        print(f"开始下载了 {url}")
        start_time = time.perf_counter()
        args = [
            f"N_m3u8DL-RE",
            url,
            "--thread-count",
            "66",
            "--save-dir",
            f"{DOWNLODS_PATH}/downloads",
            "--tmp-dir",
            f"{DOWNLODS_PATH}/tmps",
        ]
        process = await asyncio.create_subprocess_exec(
            *args, stdout=None, stderr=None
        )
        await process.wait()
        print(f"结束下载了 {url}")
        endtime = time.perf_counter()
        print(f"下载耗时 {endtime - start_time}")
        if process.returncode != 0:
            raise Exception(f"下载失败 {url}")

        return item

class UploadPipeLines:
    async def process_item(self, item, spider):
        url = item["url"]
        print(f"开始上传了 {url}")
        start_time = time.perf_counter()

        await asyncio.sleep(2)
        

        print(f"结束上传了 {url}")
        endtime = time.perf_counter()
        print(f"上传耗时 {endtime - start_time}")
        pass