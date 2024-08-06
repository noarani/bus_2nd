import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from pathlib import Path
import time
from pdf2image import convert_from_path
import glob
import keep_alive

load_dotenv('.env')
id = os.getenv('ID')
pw = os.getenv('PW')
downloadplace = str(Path(os.getenv('DOWNLOAD_PLACE')).resolve())#相対パスを絶対パスに変換
imageplace = str(Path(os.getenv('IMAGE_PLACE')).resolve())#相対パスを絶対パスに変換

TOKEN = os.getenv('DISCORD_TOKEN')

def get_bus_info():

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("prefs", {"download.default_directory": downloadplace, "download.prompt_for_download": False,  # ダウンロード時の確認ダイアログを表示しない
    "download.directory_upgrade": True,  # ダウンロードディレクトリの設定を有効化
    "plugins.always_open_pdf_externally": True  # PDF ファイルをブラウザで開かずに直接ダウンロードする
    })

    webdriver_path = ChromeDriverManager().install()
    if os.path.splitext(webdriver_path)[1] != '.exe':
        webdriver_dir_path = os.path.dirname(webdriver_path)
        webdriver_path = os.path.join(webdriver_dir_path, 'chromedriver.exe')
    chrome_service = Service(executable_path=webdriver_path)
    driver = webdriver.Chrome(service=chrome_service, options=options)

    driver.minimize_window()
    driver.get('https://portal.mc.chitose.ac.jp/portal/?0')

    wait = WebDriverWait(driver, 10)

    wait.until(EC.presence_of_all_elements_located)

    idin = driver.find_element(By.XPATH, "//*[@id=\"userID\"]")
    pwin = driver.find_element(By.XPATH, "//*[@id=\"password\"]")

    idin.send_keys(id)
    pwin.send_keys(pw)

    driver.find_element(By.XPATH, "//input[@value='ログイン']").click()#login
    

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_all_elements_located)

    handoutbtn = driver.find_element(By.XPATH,"/html/body/div/div[1]/div[3]/ul/li[2]/a")

    #handoutbtn = driver.find_element(By.XPATH,"/html/body/div/div[1]/div[3]/ul/li[2]/a")

    notificationbtn = driver.find_element(By.XPATH, "/html/body/div/div[1]/div[3]/ul/li[5]/a")
    notificationbtn.click()#配布物開く//ok

    wait.until(EC.presence_of_all_elements_located)

    file_name = "bus_schedule" + ".jpeg"

    try:
        driver.find_element(By.PARTIAL_LINK_TEXT, "シャトルバスダイヤについて").click()#「シャトルバスダイヤについて」の連絡を開く
        wait.until(EC.presence_of_all_elements_located)

        delfiles = glob.glob(downloadplace+"\\*シャトルバス時刻表*.pdf")
        # 一致したファイルをすべて削除
        for file in delfiles:
            os.remove(file)#古いpdfファイルを削除
        for file in os.scandir(imageplace):
            os.remove(file.path)#古いimageファイルを削除
        print('Deleted old bus schedule pdf and image')

        bustimepdf = driver.find_element(By.XPATH, "/html/body/div/div[3]/div/div/div[2]/div/div/div/div[2]/div/table/tbody/tr[2]/td[2]/div/ul/li/a")
        bustimepdf.click()#download

        time.sleep(10)#ダウンロード待ち
        driver.quit()
        print('Downloaded new bus notification')

        # PDF to Image
        pdf_file = glob.glob(downloadplace+"\\*シャトルバス時刻表*.pdf")

    # ここでpdf_fileがリストである場合、最初の要素を取得
        if isinstance(pdf_file, list):
            pdf_file = pdf_file[0]

        img_dir=Path(imageplace)
        page = convert_from_path(pdf_file, dpi=150)

        image_path = img_dir / file_name
        page[0].save(str(image_path), "JPEG")
        print('Converted PDF to Image')


    except NoSuchElementException:
        
        # 要素が見つからない場合の処理(すでにダウンロード済み、画像もあるはず)
        print('Undefinde new bus notification')
        driver.quit()
        image_path = Path(imageplace)/file_name

    #この時点で画像できてる//ok
    return image_path
    

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

previous_message_id = None

@client.event
async def on_ready():
    #loop.start()
    print("rdy")
    await tree.sync()#スラッシュコマンドを同期


@tasks.loop(hours=1)
async def loop():

    global previous_message_id

    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    if now.weekday()==0 and now.hour==6:
        for guild in client.guilds:
            print(guild.name)
            channel = discord.utils.get(guild.channels, name="バス")
            if channel:
                try:
                    last_message = await channel.fetch_message(channel.last_message_id)
                    try:
                        await last_message.delete()
                        embed = discord.Embed(title="シャトルバス時刻表", color=0x00ff00)
                        fname = "bus_schedule.jpeg"
                        file = discord.File(fp = get_bus_info(), filename = fname, spoiler = False)
                        embed.set_image(url = "attachment://" + fname)
                        await channel.send(file = file,embed = embed)
                    except Exception as e:
                        print(f"Error in guild {guild.name}: {e}")
                except Exception as e:
                    try:
                        embed = discord.Embed(title="シャトルバス時刻表", color=0x00ff00)
                        fname = "bus_schedule.jpeg"
                        file = discord.File(fp = get_bus_info(), filename = fname, spoiler = False)
                        embed.set_image(url = "attachment://" + fname)
                        await channel.send(file = file,embed = embed)
                    except Exception as e:
                        print(f"Error in guild {guild.name}: {e}")

@tree.command(name="bus",description="bus-scheduleを表示します")
async def bus_command(interaction: discord.Interaction):

    global previous_message_id
    
    await interaction.response.defer()
    embed = discord.Embed(title="シャトルバス時刻表", color=0x00ff00)
    fname = "bus_schedule.jpeg"
    file = discord.File(get_bus_info(), filename = fname, spoiler = False)
    embed.set_image(url = "attachment://" + fname)

    if previous_message_id:
        try:
            previous_message = await interaction.channel.fetch_message(previous_message_id)
            await previous_message.delete()
        except discord.NotFound:
            pass  # メッセージが見つからない場合は無視

    # 新しいメッセージを送信
    message = await interaction.followup.send(file=file, embed=embed)
    # 新しいメッセージIDを保存
    previous_message_id = message.id

    


                    


keep_alive.keep_alive()
client.run(TOKEN)
















