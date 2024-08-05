import datetime
import os
from PyQt5.QtCore import QObject, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import threading
import debugpy
import pandas as pd
from bs4 import BeautifulSoup
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
    
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
start_page = 1
end_page = 1
# 웹 페이지 열기
test = '모니터'
url = f'https://search.11st.co.kr/pc/total-search?kwd={test}'
driver.get(url)
# 페이지 로딩 대기
time.sleep(5)
# 상품 링크 저장 리스트
product_links = []

for page in range(start_page, end_page + 1):
    try:
        product_list_items = driver.find_elements(By.CLASS_NAME, "c-search-list__item")
        
        for item in product_list_items:
            try:
                # Extract the seller link
                seller_name_div = item.find_element(By.CLASS_NAME, "c-seller__name")
                link_element = seller_name_div.find_element(By.TAG_NAME, "a")
                seller_link = link_element.get_attribute('href')
                product_links.append(seller_link)
            except Exception as e:
                print(f"Error processing item: {e}")
                continue
    except Exception as e:
        print(f"Error processing page: {e}")
        continue
    # 다음 페이지로 이동
    try:
        # Click the button in the section with id 'section_plusPrd'
        next_button_plusPrd = driver.find_element(By.XPATH, f"//section[@id='section_plusPrd']//button[text()='{page}']")
        next_button_plusPrd.click()
        time.sleep(5)  # Wait for the page to load
        
        # Click the button in the section with id 'section_commonPrd'
        next_button_commonPrd = driver.find_element(By.XPATH, f"//section[@id='section_commonPrd']//button[text()='{page}']")
        next_button_commonPrd.click()
        time.sleep(5)  # Wait for the page to load
    except Exception as e:
        print(e)
        
print(product_links)

num_threads = 3
chunk_size = len(product_links) // num_threads
if len(product_links) % num_threads:
    chunk_size += 1

vendor_info_list =[]
for link in product_links:

    # Fetch the HTML content of the webpage
    response = requests.get(link)
    html_content = response.text

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Locate the store_info_detail element
    store_info_detail = soup.find('dl', class_='store_info_detail')

    # Initialize variables for the desired information
    store_info = {}

    if store_info_detail:
        details = store_info_detail.find_all('dd')

        # Extract and store the desired information
        store_info["업체명"] = "11번가"
        store_info["상호/대표자"] = details[1].text.strip() if len(details) > 1 else "N/A"
        store_info["연락처"] = details[5].text.strip() if len(details) > 5 else "N/A"
        store_info["사업장소재지"] = details[7].text.strip() if len(details) > 7 else "N/A"

    # Print the extracted information
    print(store_info)

    # Assuming vendor_info_list is a predefined list to store the extracted information
    vendor_info_list = []
    vendor_info_list.append(store_info)