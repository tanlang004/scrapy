# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import asyncio
import time
from pathlib import Path
import httpx
import os
from typing import Optional

DOWNLODS_PATH = Path.home().absolute()

OPEN_LIST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwicHdkX3RzIjowLCJleHAiOjE3NzE5NTk3OTEsIm5iZiI6MTc3MTc4Njk5MSwiaWF0IjoxNzcxNzg2OTkxfQ.FourpR5zRTScsBWHiIufWKXvJWlNVtmvgiDgLJkC3WQ"

OPEN_LIST_BASE_URL = "https://5244.xiaodu1234.xyz/"
OPEN_LIST_UPLOAD_URL = OPEN_LIST_BASE_URL + "api/fs/put"


# -------------------------- 配置参数（替换为你的实际信息）--------------------------
OPENLIST_URL = "https://5244.xiaodu1234.xyz"  # 你的OpenList部署地址（无末尾/）
USERNAME = "admin"  # OpenList登录账号
PASSWORD = "123321"  # OpenList登录密码
LOCAL_VIDEO_PATH = f"{DOWNLODS_PATH}/downloads/02f0b2d4731158d97e7c9b65dd1087f9_2026-02-22_15-45-13.mp4"  # 本地视频文件路径
OPENLIST_TARGET_PATH = "/天翼云盘/02f0b2d4731158d97e7c9b65dd1087f9_2026-02-22_15-45-13.mp4"  # OpenList目标路径（官方要求path头格式）
# ---------------------------------------------------------------------------------


async def get_openlist_bearer_token_async(
    openlist_url: str, username: str, password: str
) -> str:
    """
    【异步版】登录OpenList获取Bearer Token（适配官方/api/auth/login接口）
    :return: 完整的Bearer Token，格式`Bearer xxxxxx`
    """
    login_url = f"{openlist_url}/api/auth/login"
    print("开始登录了", login_url)
    payload = {"username": username, "password": password}
    try:
        # 异步客户端：httpx.AsyncClient（核心区别）
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.post(login_url, json=payload)  # 异步请求加await
            res.raise_for_status()
            result = res.json()
            if result.get("success") and result.get("data", {}).get("token"):
                token = result["data"]["token"]
                print(f"✅ 异步登录成功，Bearer Token：{token[:20]}...")
                return f"Bearer {token}"
            else:
                raise Exception(f"登录失败：{result.get('message', '未知错误')}")
    except Exception as e:
        raise Exception(f"异步获取Token失败：{str(e)}")


async def upload_video_by_official_api_async(
    openlist_url: str,
    bearer_token: str,
    local_file_path: str,
    target_path: str,
    as_task: Optional[bool] = True,
    last_modified: Optional[int] = None,
) -> bool:
    """
    【异步版】按OpenList官方API流式上传视频（PUT /api/fs/put）
    核心：异步流式上传，边读边发，不阻塞主线程
    """
    # 校验本地文件
    if not os.path.exists(local_file_path):
        raise FileNotFoundError(f"本地文件不存在：{local_file_path}")

    # 构造官方要求的请求头（和同步版一致）
    headers = {
        "Authorization": bearer_token,
        "path": target_path,
        "As-Task": str(as_task).lower(),  # 必须小写true/false
    }
    # 可选：设置文件修改时间（毫秒级Unix时间戳）
    if last_modified is None:
        local_mtime = os.path.getmtime(local_file_path)
        headers["Last-Modified"] = str(int(local_mtime * 1000))

    upload_url = f"{openlist_url}/api/fs/put"
    file_size = os.path.getsize(local_file_path)
    print(
        f"\n📤 开始异步流式上传：{local_file_path}（大小：{file_size/1024/1024:.2f}MB）"
    )
    print(f"🎯 目标路径：{target_path}")

    try:
        # 异步客户端 + 异步文件读取（核心）
        async with httpx.AsyncClient(timeout=3000) as client:  # 大文件超时设5分钟
            # 以二进制流方式异步读取文件（边读边发，不占内存）
            with open(local_file_path, "rb") as f:
                # 异步PUT请求：content传文件句柄，自动流式发送
                res = await client.put(url=upload_url, headers=headers, content=f)
                res.raise_for_status()
                result = res.json()
                if result.get("code") == 200 and result.get("message") == "success":
                    print("✅ 异步上传成功（OpenList官方API）！")
                    return True
                else:
                    raise Exception(
                        f"上传失败：{result.get('message', '官方未返回原因')}"
                    )
    except Exception as e:
        raise Exception(f"异步上传异常：{str(e)}")


async def batch_upload_videos_async(
    openlist_url: str,
    bearer_token: str,
    video_list: list[tuple[str, str]],  # 列表元素：(本地路径, 目标路径)
) -> None:
    """
    【扩展】异步批量上传多个视频（核心优势：并发上传，效率翻倍）
    :param video_list: 示例 [("./video1.mp4", "/videos/v1.mp4"), ("./video2.mp4", "/videos/v2.mp4")]
    """
    # 创建所有上传任务（并发执行）
    tasks = [
        upload_video_by_official_api_async(
            openlist_url=openlist_url,
            bearer_token=bearer_token,
            local_file_path=local_path,
            target_path=target_path,
        )
        for local_path, target_path in video_list
    ]
    # 并发执行所有上传任务
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 统计结果
    success_count = 0
    fail_count = 0
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            fail_count += 1
            print(f"❌ 第{idx+1}个视频上传失败：{str(result)}")
        elif result is True:
            success_count += 1
    print(f"\n📊 批量上传完成：成功{success_count}个，失败{fail_count}个")


class JablePipeline:
    async def process_item(self, item, spider):
        url = item["url"]
        print(f"开始下载了 {url}")
        start_time = time.perf_counter()
        args = [
            f"N_m3u8DL-RE",
            url,
            "--thread-count",
            "333",
            "--save-dir",
            f"{DOWNLODS_PATH}/downloads",
            "--tmp-dir",
            f"{DOWNLODS_PATH}/tmps",
        ]
        process = await asyncio.create_subprocess_exec(*args, stdout=None, stderr=None)
        await process.wait()
        print(f"\n结束下载了 {url}")
        endtime = time.perf_counter()
        print(f"下载耗时 {endtime - start_time}")
        if process.returncode != 0:
            raise Exception(f"下载失败 {url}")

        return item


class UploadPipeLines:
    async def process_item(self, item, spider):
        url = item["url"]
        print(f"\n开始上传了 {url}")
        start_time = time.perf_counter()

        await asyncio.sleep(1)

        token = await get_openlist_bearer_token_async(OPENLIST_URL, USERNAME, PASSWORD)

        result = await upload_video_by_official_api_async(
            OPENLIST_URL, token, LOCAL_VIDEO_PATH, OPENLIST_TARGET_PATH
        )
        print("上传结果", result)
        print(f"结束上传了 {url}")
        endtime = time.perf_counter()
        print(f"上传耗时 {endtime - start_time}")
        pass
