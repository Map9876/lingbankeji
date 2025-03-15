import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# 配置
LOGIN_URL = "https://aiapi.lingbankeji.com/admin/auth/login"
TARGET_URL = "https://aimain.lingbankeji.com"  # 要备份的目标页面
OUTPUT_DIR = "backup"  # 备份文件保存目录
USERNAME = "admin"
PASSWORD = "admin"

# 初始化 Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # 无头模式
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--remote-debugging-port=9222")

# 启动 Chrome 浏览器
driver = webdriver.Chrome(service=Service(), options=chrome_options)

# 登录并获取 token
def login():
    driver.get(LOGIN_URL)
    time.sleep(3)  # 等待页面加载

    # 填写登录表单
    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")
    username_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)

    time.sleep(3)  # 等待登录完成

    # 获取登录后的 token（假设返回的 token 在页面中）
    token = driver.execute_script("return localStorage.getItem('token');")
    return token

# 备份页面资源
def backup_page(url, token):
    # 设置请求头
    headers = {
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
        "token": token,
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    # 获取页面内容
    driver.get(url)
    time.sleep(5)  # 等待页面完全加载

    # 获取页面 HTML
    html = driver.page_source
    save_file(os.path.join(OUTPUT_DIR, "index.html"), html)

    # 获取所有资源（CSS、JS、图片等）
    resources = driver.execute_script("""
        return performance.getEntriesByType('resource').map(resource => ({
            url: resource.name,
            type: resource.initiatorType
        }));
    """)

    # 下载并保存资源
    for resource in resources:
        resource_url = resource["url"]
        resource_type = resource["type"]
        if resource_url.startswith("http"):
            try:
                response = requests.get(resource_url, headers=headers)
                if response.status_code == 200:
                    # 保存资源
                    file_path = os.path.join(OUTPUT_DIR, resource_url.split("//")[1])
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    save_file(file_path, response.content)
            except Exception as e:
                print(f"Failed to download {resource_url}: {e}")

# 保存文件
def save_file(path, content):
    with open(path, "wb" if isinstance(content, bytes) else "w") as f:
        f.write(content)
    print(f"Saved: {path}")

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
    backup_page(TARGET_URL, token)

    # 关闭浏览器
    driver.quit()

if __name__ == "__main__":
    main()
