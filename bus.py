from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pathlib import Path
import time
from pdf2image import convert_from_path

load_dotenv('.env')
id = os.getenv('ID')
pw = os.getenv('PW')
downloadplace = os.getenv('DOWNLOAD_PLACE')
imageplace = os.getenv('IMAGE_PLACE')

driver = webdriver.Chrome()

options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", {
    "download.default_directory":os.getcwd()+downloadplace, #ダウンロード先のフォルダ
    "plugins.always_open_pdf_externally": True              #PDFをブラウザのビューワーで開かせない
})


driver.get('https://portal.mc.chitose.ac.jp/portal/?0')

idin = driver.find_element(By.XPATH, "//*[@id=\"userID\"]")
pwin = driver.find_element(By.XPATH, "//*[@id=\"password\"]")

idin.send_keys(id)
pwin.send_keys(pw)

driver.find_element(By.XPATH, "/html/body/div/div[4]/form/div[3]/div/input").click()

wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_all_elements_located)

notificationbtn = driver.find_element(By.XPATH, "/html/body/div/div[3]/div/div/div[2]/div/div[1]/div/div/div/div/dl[1]/dd/a/span")
notificationbtn.click()

wait.until(EC.presence_of_all_elements_located)

notification_box = driver.find_element(By.XPATH, "/html/body/div/div[3]/div/div/div[2]/div/div[1]/div/div[2]/div/div/form/div[3]/table/tbody")
elements = notification_box.find_elements(By.XPATH, "tr")[1:]
has_bus_notification = False
for element in elements:
    title = element.find_element(By.XPATH, "td[4]")
    if title.text.startswith('シャトルバスダイヤについて'):#シャトルバスダイヤについてから始まる連絡があったら
        title.click()#クリックして開く

        has_bus_notification = True

        wait.until(EC.presence_of_all_elements_located)

        for file in os.scandir(downloadplace):
            os.remove(file.path)#古いpdfファイルを削除

        for file in os.scandir(imageplace):
            os.remove(file.path)#古いimageファイルを削除
        
        bustime = driver.find_element(By.XPATH, "/html/body/div/div[3]/div/div/div[2]/div/div/div/div[2]/div/table/tbody/tr[2]/td[2]/div/ul/li/a")
        bustime.click()#download
        time.sleep(10)
        driver.quit()

        # PDF to Image
        pdf_path = Path('.*シャトルバス時刻表.*.pdf')
        img_dir=Path(imageplace)
        pages = convert_from_path(pdf_path, dpi=150)
        file_name = "シャトルバス時刻表" + ".jpeg"
        image_path = img_dir / file_name
        pages[0].save(str(image_path), "JPEG")

        break

if not has_bus_notification:#なかったら次に進む(すでにダウンロード済み、画像もあるはず)
    print('No new bus notification')
    driver.quit()
    exit()

#この時点で画像できてる













