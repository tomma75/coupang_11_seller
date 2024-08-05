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
import psutil
import asyncio
import aiohttp

class crawling(QObject):
    returnMaxPb = pyqtSignal(int)
    ReturnError = pyqtSignal(str)
    returnPb = pyqtSignal(int)
    returnPb2 = pyqtSignal(int)
    returnWarning = pyqtSignal(str)

    def __init__(self, isdebug, search_input, threading_input, pages_input1, pages_input2):
        super().__init__()
        self.isdebug = isdebug
        self.search_input = search_input
        self.threading_input = int(threading_input)
        self.pages_input1 = int(pages_input1)
        self.pages_input2 = int(pages_input2)
        self.processed_links = 0

    def run(self):
        try:
            if self.isdebug:
                debugpy.debug_this_thread()
            maxPb = 100
            self.returnMaxPb.emit(maxPb)
            self.returnPb.emit(10)
            if self.pages_input1 != 0:
                driver, option, product_links = self.list_find_coupang(self.pages_input1, self.search_input)
                self.returnWarning.emit(f'쿠팡 웹페이지 리스트업 완료!( 1 / 4 )_{len(product_links)}')
                self.returnWarning.emit(f'쿠팡 웹페이지 {len(product_links)}개 추출 완료')
            self.returnPb.emit(20)
            if self.pages_input1 != 0:
                self.get_information_coupang(option, product_links, self.threading_input, self.search_input)
                self.returnWarning.emit(f'쿠팡 데이터 추출 완료!( 2 / 4 )')
            self.returnPb.emit(40)
            
            self.returnPb.emit(60)
            if self.pages_input2 != 0:
                product_links2 = self.list_find_11st(self.pages_input2, self.search_input)
                self.returnWarning.emit(f'11번가 웹페이지 리스트업 완료!( 3 / 4 )')
                self.returnWarning.emit(f'11번가 웹페이지 {len(product_links2)}개 추출 완료')
            self.returnPb.emit(80)
            if self.pages_input2 != 0:
                total_links = len(product_links2)
                asyncio.run(self.get_information_11st_async(product_links2, total_links, self.search_input))
                self.returnWarning.emit(f'11번가 데이터 추출 완료!( 4 / 4 )')
            self.returnPb.emit(100)
            self.returnPb2.emit(total_links)

        except Exception as e:
            self.ReturnError.emit(f'Main FLOW ERR : {str(e)}')

    async def fetch(self, session, url):
        try:
            async with session.get(url) as response:
                return await response.text()
        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return None

    async def process_link(self, session, link, vendor_info_list, total_links):
        html_content = await self.fetch(session, link)
        if html_content is None:
            return

        soup = BeautifulSoup(html_content, 'html.parser')
        store_info_detail = soup.find('dl', class_='store_info_detail')

        store_info = {}
        if store_info_detail:
            details = store_info_detail.find_all('dd')
            store_info["업체명"] = "11번가"
            store_info["상호/대표자"] = details[1].text.strip() if len(details) > 1 else "N/A"
            store_info["연락처"] = details[5].text.strip() if len(details) > 5 else "N/A"
            store_info["사업장소재지"] = details[7].text.strip() if len(details) > 7 else "N/A"

        if store_info.get("상호/대표자") != "N/A":
            vendor_info_list.append(store_info)
        
        # Update progress
        self.processed_links += 1
        progress = int((self.processed_links / total_links) * 100)
        self.returnPb2.emit(progress)

    async def get_information_11st_async(self, product_links, total_links, search_input):
        vendor_info_list = []
        async with aiohttp.ClientSession() as session:
            tasks = [self.process_link(session, link, vendor_info_list, total_links) for link in product_links]
            await asyncio.gather(*tasks)

        df = pd.DataFrame(vendor_info_list, columns=["업체명", "상호/대표자", "연락처", "사업장소재지"])
        output_dir = "./output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file = os.path.join(output_dir, f"추출물(11번가_{search_input})_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx")
        with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, index=False)

    def get_information_11st(self, product_links, num_thread,search_input):
        try:
            num_threads = num_thread
            chunk_size = len(product_links) // num_threads
            if len(product_links) % num_threads:
                chunk_size += 1

            def process_links(links,search_input):
                vendor_info_list = []
                for link in links:
                    try:
                        response = requests.get(link)
                        html_content = response.text

                        soup = BeautifulSoup(html_content, 'html.parser')

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

                        # Assuming vendor_info_list is a predefined list to store the extracted information
                        if ["상호/대표자"] == "N/A":
                            continue
                        vendor_info_list.append(store_info)
                    except Exception as e:
                        print(f"Error processing page: {e}")
                        continue

                df = pd.DataFrame(vendor_info_list, columns=["업체명", "상호/대표자", "연락처", "사업장소재지"])
                # Define the output directory and file name
                output_dir = "./output"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                output_file = os.path.join(output_dir, f"추출물(11번가_{search_input})_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx")
                
                with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
                    df.to_excel(writer, index=False)

            # 스레드 리스트 생성
            threads = []
            for i in range(0, len(product_links), chunk_size):
                thread_links = product_links[i:i + chunk_size]
                thread = threading.Thread(target=process_links, args=(thread_links,search_input,))
                threads.append(thread)

            # 스레드 시작
            for thread in threads:
                thread.start()

            # 스레드 종료 대기
            for thread in threads:
                thread.join()
        except Exception as e:
            self.ReturnError.emit(f'get_information ERR : {str(e)}')
            raise
    def list_find_11st(self, get_end_page, search_input):
        for process in psutil.process_iter():
            if process.name() == "chromedriver.exe":
                process.kill()
                
        driver_path = ChromeDriverManager().install()
        
        options = webdriver.ChromeOptions()
        options.binary_location = r".\Chrome\Application\chrome.exe"
        options.add_argument("--disable-blink-features=AutomationControlled")
        service = Service(driver_path, log_path="chromedriver.log")
        driver = webdriver.Chrome(service=service, options=options)
        start_page = 1
        end_page = get_end_page
        # 웹 페이지 열기
        input = search_input
        url = f'https://search.11st.co.kr/pc/total-search?kwd={input}'
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
                if page == 1:
                    continue
                else:
                    # Click the button in the section with id 'section_plusPrd'
                    next_button_plusPrd = driver.find_element(By.XPATH, f"//section[@id='section_plusPrd']//button[text()='{page}']")
                    next_button_plusPrd.click()
                    time.sleep(5)  # Wait for the page to load
                    
                    # Click the button in the section with id 'section_commonPrd'
                    next_button_commonPrd = driver.find_element(By.XPATH, f"//section[@id='section_commonPrd']//button[text()='{page}']")
                    next_button_commonPrd.click()
                    time.sleep(5)  # Wait for the page to load
            except Exception as e:
                self.ReturnError.emit(f'list_find ERR : {str(e)}')
                raise
        return product_links

    def list_find_coupang(self, get_end_page, search_input):
        for process in psutil.process_iter():
            if process.name() == "chromedriver.exe":
                process.kill()
                
        driver_path = ChromeDriverManager().install()
        
        options = webdriver.ChromeOptions()
        options.binary_location = r".\Chrome\Application\chrome.exe"
        options.add_argument("--disable-blink-features=AutomationControlled")
        service = Service(driver_path, log_path="chromedriver.log")
        driver = webdriver.Chrome(service=service, options=options)
        start_page = 1
        end_page = get_end_page
        # 웹 페이지 열기
        url = f'https://www.coupang.com/np/search?component=&q={search_input}&channel=user'
        driver.get(url)
        # 페이지 로딩 대기
        time.sleep(5)
        # 상품 링크 저장 리스트
        product_links = []

        for page in range(start_page, end_page + 1):
            # 상품 리스트 가져오기
            product_list = driver.find_element(By.XPATH, "//ul[@id='productList']")
            products = product_list.find_elements(By.TAG_NAME, "li")

            for product in products:
                try:
                    # 광고 상품인 경우 스킵
                    if 'search-product__ad-badge' in product.get_attribute('class'):
                        continue
                    
                    # 상품 링크 추출
                    link_element = product.find_element(By.TAG_NAME, "a")
                    product_link = link_element.get_attribute('href')
                    
                    # 링크 끝에 rank= 가 포함된 링크만 저장
                    if 'rank=' in product_link:
                        product_links.append(product_link)
                except Exception as e:
                    print(f"Error processing product: {e}")
            
            # 다음 페이지로 이동
            try:
                if page == 1:
                    continue
                else:
                    next_button = driver.find_element(By.CLASS_NAME, "btn-next")
                    next_button.click()
                    time.sleep(5)  # 페이지 로딩 대기
            except Exception as e:
                self.ReturnError.emit(f'list_find ERR : {str(e)}')
                raise
        return driver, options, product_links

    def get_information_coupang(self, options, product_links, num_thread,search_input):
        try:
            num_threads = num_thread
            chunk_size = len(product_links) // num_threads
            if len(product_links) % num_threads:
                chunk_size += 1

            def process_links(links,search_input):
                local_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                vendor_info_list = []

                for link in links:
                    local_driver.get(link)
                    time.sleep(5)  # 페이지 로딩 대기

                    try:
                        # 판매자 링크 클릭
                        vendor_link_element = local_driver.find_element(By.CSS_SELECTOR, "div.prod-sale-vendor a.prod-sale-vendor-name")
                        vendor_link = vendor_link_element.get_attribute('href')
                        local_driver.get(vendor_link)
                        time.sleep(5)  # 페이지 로딩 대기

                        # 가게 평가 버튼 클릭
                        rating_button = local_driver.find_element(By.CSS_SELECTOR, "div.store-rating button")
                        rating_button.click()
                        time.sleep(5)  # 페이지 로딩 대기

                        # 정보 추출
                        store_info = {}
                        store_info["업체명"] = "쿠팡"
                        store_info["상호/대표자"] = local_driver.find_element(By.XPATH, "//th[contains(text(), '상호/ 대표자')]/following-sibling::td").text
                        store_info["연락처"] = local_driver.find_element(By.XPATH, "//th[contains(text(), '연락처')]/following-sibling::td").text
                        store_info["사업장소재지"] = local_driver.find_element(By.XPATH, "//th[contains(text(), '사업장소재지')]/following-sibling::td").text

                        vendor_info_list.append(store_info)
                    except Exception as e:
                        self.ReturnError.emit(f'쿠팡전용링크 : {str(e)}')
                        continue
                
                local_driver.quit()
                df = pd.DataFrame(vendor_info_list, columns=["업체명", "상호/대표자", "연락처", "사업장소재지"])
                # Define the output directory and file name
                output_dir = "./output"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                output_file = os.path.join(output_dir, f"추출물(쿠팡_{search_input})_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx")
                
                with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
                    df.to_excel(writer, index=False)

            # 스레드 리스트 생성
            threads = []
            for i in range(0, len(product_links), chunk_size):
                thread_links = product_links[i:i + chunk_size]
                thread = threading.Thread(target=process_links, args=(thread_links,search_input,))
                threads.append(thread)

            # 스레드 시작
            for thread in threads:
                thread.start()

            # 스레드 종료 대기
            for thread in threads:
                thread.join()
        except Exception as e:
            self.ReturnError.emit(f'get_information ERR : {str(e)}')
            raise