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
import platform




load_dotenv('.env')
id = os.getenv('ID')
pw = os.getenv('PW')
downloadplace = str(Path(os.getenv('DOWNLOAD_PLACE')).resolve())#相対パスを絶対パスに変換
imageplace = str(Path(os.getenv('IMAGE_PLACE')).resolve())#相対パスを絶対パスに変換
if platform.system() == "Windows":
    poppler_path = str(Path(os.getenv('POPPLER_PATH')).resolve())
else:
    poppler_path = ""  # LinuxではPATHが通っていれば空でOK
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

    # ChromeDriverのパスを取得
    driver = webdriver.Chrome(options=options)

    print('ChromeDriver started')

    driver.maximize_window()
    driver.get('https://portal.mc.chitose.ac.jp/portal/?0')

    print('Accessed portal')

    wait = WebDriverWait(driver, 10)

    wait.until(EC.presence_of_all_elements_located)

    idin = driver.find_element(By.CSS_SELECTOR, "#username")
    pwin = driver.find_element(By.CSS_SELECTOR, "#password")

    idin.send_keys(id)
    pwin.send_keys(pw)

    

    login_button = driver.find_element(By.CSS_SELECTOR,"#login")#login
    driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
    driver.execute_script("arguments[0].click();", login_button)
    

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_all_elements_located)

    # handoutbtn = driver.find_element(By.LINK_TEXT,"配布物")

    #handoutbtn = driver.find_element(By.XPATH,"/html/body/div/div[1]/div[3]/ul/li[2]/a")

    # notificationbtn = driver.find_element(By.CSS_SELECTOR, "#menu > div.offcanvas-body.d-block.p-0 > ul > li:nth-child(2) > a")
    # notificationbtn.click()#連絡開く//ok
    driver.get("https://portal.mc.chitose.ac.jp/portal/OfficeMemo/ViewReceivedTitles?currentPage=1&filter=all&searchKeyword=&c_filter=office")

    wait.until(EC.presence_of_all_elements_located)


    file_name = "bus_schedule" + ".jpeg"

    try:

        print('Clicked notification')
        links = driver.find_elements(By.XPATH, "//a[contains(text(), 'シャトルバスについて')]")
        bus_schedule_element = None
        for link in links:
            if "シャトルバスについて" in link.text:
                bus_schedule_element = link
                break

        if bus_schedule_element is None:
            raise NoSuchElementException("バスダイヤのお知らせが見つかりませんでした。")

        
        driver.execute_script("arguments[0].scrollIntoView(true);", bus_schedule_element)  # 要素を画面内にスクロール
        driver.execute_script("arguments[0].click();", bus_schedule_element)
        wait.until(EC.presence_of_all_elements_located)

        print('Clicked bus schedule notification')

        delfiles = glob.glob(downloadplace+"*シャトルバス時刻表*.pdf")
        # 一致したファイルをすべて削除
        for file in delfiles:
            os.remove(file)#古いpdfファイルを削除
        for file in os.scandir(imageplace):
            os.remove(file.path)#古いimageファイルを削除
        print('Deleted old bus schedule pdf and image')

        bustimepdf = driver.find_element(By.CSS_SELECTOR, "a[class='filename'][href]")
        driver.execute_script("arguments[0].click();", bustimepdf)

        time.sleep(10)#ダウンロード待ち
        driver.quit()
        print('Downloaded new bus notification')

        # PDF to Image
        pdf_file = glob.glob(os.path.join(downloadplace, "*シャトルバス時刻表*.pdf"))
        print(pdf_file)

        if not pdf_file:
            raise NoSuchElementException("PDFファイルが見つかりませんでした。")

        pdf_file = pdf_file[0]

        img_dir = Path(imageplace)
        page = convert_from_path(pdf_file, dpi=300, poppler_path=poppler_path)

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
    


# get_bus_info()#初回実行

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

previous_message_id = None

@client.event
async def on_ready():
    #loop.start()
    print("rdy")
    await tree.sync()#スラッシュコマンドを同期

@tasks.loop(hours=24)
async def loop():

    @tasks.loop(hours=1)
    async def loop():

        global previous_message_id

        now = datetime.now(ZoneInfo("Asia/Tokyo"))
        if now.weekday() in (5, 6, 0):  # 土曜日か日曜日か月曜日の場合
            embed = discord.Embed()
            fname = "シャトルバス時刻表.jpeg"
            file = discord.File(fp=get_bus_info(), filename=fname, spoiler=False)
            embed.set_image(url="attachment://" + fname)

            # ここで特定のチャンネルにメッセージを送信
            for guild in client.guilds:
                channel = discord.utils.get(guild.channels, name="バス")
                if channel:
                    await channel.send(embed=embed, file=file)


@tree.command(name="bus",description="bus-scheduleを表示します")
async def bus_command(interaction: discord.Interaction):

    global previous_message_id
    
    try:
        await interaction.response.defer()  # 応答を遅延
    except discord.errors.NotFound:
        print("Interaction not found or expired.")
        return
    
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

#@client.event
#async def on_message(message):
#    if message.content == '/cleanup':
#        if message.author.guild_permissions.administrator:
#            await message.channel.purge()
#            await message.channel.send('塵一つ残らないね！')
#        else:
#            await message.channel.send('何様のつもり？')

@tree.command(name="cleanup", description="チャンネルのメッセージを削除します")
async def cleanup_command(interaction: discord.Interaction):
    try:
        await interaction.response.defer()
    except discord.errors.NotFound:
        print("Interaction not found or expired.")
        return

    if interaction.user.guild_permissions.administrator:
        try:
            # コマンド実行メッセージ以外を削除
            def not_command_message(msg):
                return msg.id != interaction.message.id

            await interaction.channel.purge(check=not_command_message)
            await interaction.followup.send('塵一つ残らないね！')
        except discord.Forbidden:
            await interaction.followup.send('ボットにメッセージ削除の権限がありません。')
    else:
        await interaction.followup.send('何様のつもり？')


keep_alive.keep_alive()
client.run(TOKEN)