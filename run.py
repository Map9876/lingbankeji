import os
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse

# 配置
LOGIN_URL = "https://aiapi.lingbankeji.com/admin/auth/login"  # 登录 API 地址
TARGET_URL = "https://aimain.lingbankeji.com"  # 要备份的目标页面
OUTPUT_DIR = "backup"  # 备份文件保存目录
USERNAME = "admin"
PASSWORD = "admin"

# 请求头
HEADERS = {
    "authority": "aiapi.lingbankeji.com",
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/json",
    "origin": "https://aimain.lingbankeji.com",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

# 登录并获取 token
def login():
    # 构造登录请求的 payload
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }

    # 发送登录请求
    try:
        response = requests.post(LOGIN_URL, headers=HEADERS, json=payload)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()  # 解析返回的 JSON 数据

        # 提取 token
        if data.get("code") == 200:
            token = data.get("data")
            print(f"Login successful! Token: {token}")
            return token
        else:
            print(f"Login failed: {data.get('message')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Login request failed: {e}")
        return None

# 下载并保存资源
def download_resource(url, output_dir, headers=None):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功

        # 解析 URL 路径
        parsed_url = urlparse(url)
        path = parsed_url.path.lstrip("/")
        if not path:
            path = "index.html"  # 默认保存为 index.html

        # 创建目录并保存文件
        file_path = os.path.join(output_dir, path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {url} -> {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")

# 使用 Selenium 监听网络请求并下载所有资源
def backup_page(url, output_dir, token):
    # 初始化 Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # 启动 Chrome 浏览器
    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    # 设置请求头，包含 token
    headers = HEADERS.copy()
    headers["token"] = token

    # 打开目标页面
    driver.get(url)
    time.sleep(5)  # 等待页面完全加载

    # 获取所有网络请求
    performance_log = driver.get_log("performance")
    resources = set()

    for entry in performance_log:
        message = json.loads(entry["message"])["message"]
        if message["method"] == "Network.requestWillBeSent":
            request = message["params"]["request"]
            url = request["url"]
            resources.add(url)  # 不进行过滤，直接保存所有 URL

    # 下载所有资源
    for resource_url in resources:
        download_resource(resource_url, output_dir, headers)

    # 关闭浏览器
    driver.quit()

# 主函数
def main():
    # 创建备份目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 登录并获取 token
    token = login()
    if not token:
        print("Login failed!")
        return

    # 备份目标页面
    backup_page(TARGET_URL, OUTPUT_DIR, token)

if __name__ == "__main__":
    main()
