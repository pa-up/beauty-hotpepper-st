from flask import Flask, render_template, request , send_file
import os
import sys
import csv
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select


# このアプリフォルダの絶対パスを取得
this_file_abspath = os.path.abspath(sys.argv[0])
last_slash_index = this_file_abspath.rfind('/')  # 最後の '/' のインデックスを取得
this_app_root_abspath = this_file_abspath[:last_slash_index]

# flaskアプリの明示
templates_path = os.path.join(this_app_root_abspath, 'templates')
static_path = os.path.join(this_app_root_abspath, 'static')
app = Flask(__name__ , template_folder=templates_path, static_folder=static_path)

# パスの定義
img_path_from_static = "img/"
csv_path_from_static = "/media/output.csv"
csv_path = static_path + "/media/output.csv"


def browser_setup(browse_visually = "no"):
    """ブラウザを起動する関数"""
    #ブラウザの設定
    options = webdriver.ChromeOptions()
    if browse_visually == "no":
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    #ブラウザの起動
    browser = webdriver.Chrome(options=options , service=ChromeService(ChromeDriverManager().install()))
    browser.implicitly_wait(3)
    return browser


def list_to_csv(to_csv_list: list , csv_path: str = "output.csv"):
    """ 多次元リストのデータをcsvファイルに保存する関数 """
    with open(csv_path, 'w' , encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(to_csv_list)


def html_table_tag_to_csv_list(table_tag_str: str, header_exist: bool = True):
    table_soup = BeautifulSoup(table_tag_str, 'html.parser')
    rows = []
    if header_exist:
        for tr in table_soup.find_all('tr'):
            cols = [] 
            for td in tr.find_all(['td', 'th']):
                cols.append(td.text.strip())
            rows.append(cols)
    else:
        for tbody in table_soup.find_all('tbody'):
            for tr in tbody.find_all('tr'):
                cols = [td.text.strip() for td in tr.find_all(['td', 'th'])]
                rows.append(cols)
    return rows


def get_building_number(page_count_info: str):
    # 正規表現を使用して物件の件数を抽出する関数
    numbers = re.findall(r'\d+', page_count_info)
    # 数字が3つ以上見つかった場合、それぞれの数字を返す
    if len(numbers) >= 3:
        start_number = int(numbers[0])
        end_number = int(numbers[1])
        total_number = int(numbers[2])
        return start_number, end_number, total_number
    else:
        return None


def scraping_reins(
        driver: WebDriverWait , 
        user_id: str , 
        password: str ,
    ):
    # ドライバーの待機時間の設定
    wait_time = 5
    wait_driver = WebDriverWait(driver, wait_time)

    # ログインボタンをクリック
    my_page_link = wait_driver.until(EC.presence_of_element_located((By.LINK_TEXT, "マイページ")))
    my_page_link.click()

    # フォームにログイン認証情報を入力
    email_form = wait_driver.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
    email_form.send_keys(user_id)
    password_form = wait_driver.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
    password_form.send_keys(password)
    time.sleep(0.5)
    login_button = wait_driver.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'ログイン')]")))
    login_button.click()

    # 予約したことのがあるサロン名を抽出
    reserved_salons_type_elements = wait_driver.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.pL15")))
    reserved_salons_list = []
    reserved_salons_list.append(["サロン名" , "サロンページURL"])
    print(f"len(reserved_salons_type_elements) : {len(reserved_salons_type_elements)}")
    for reserved_salons_type_element in reserved_salons_type_elements:
        reserved_salons_element_list = reserved_salons_type_element.find_elements(By.TAG_NAME, "li")
        print(f"len(reserved_salons_element_list) : {len(reserved_salons_element_list)}")
        for reserved_salon_element in reserved_salons_element_list:
            salon_name = reserved_salon_element.find_element(By.CSS_SELECTOR, "p.b").text
            salon_page_link = reserved_salon_element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            reserved_salons_list.append([salon_name , salon_page_link])

    driver.quit()

    return reserved_salons_list



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST' and request.form['start_scraping'] == "true":
        # フォームからログイン認証情報を取得
        user_id = request.form['user_id']
        password = request.form['password']

        # ページにアクセス
        searched_url = "https://beauty.hotpepper.jp/"
        browse_visually = request.form['browse_visually'] 
        driver = browser_setup(browse_visually)

        # スクレイピング開始
        driver.get(searched_url)
        to_csv_list: list = scraping_reins(
            driver , user_id , password ,
        )

        # リストをCSVファイルに保存
        list_to_csv(
            to_csv_list = to_csv_list ,
            csv_path = csv_path ,
        )
        return render_template(
            "index.html" ,
            img_path_from_static = img_path_from_static ,
            csv_path_from_static = csv_path_from_static ,
        )

    else:
        return render_template(
            "index.html" ,
            img_path_from_static = img_path_from_static ,
            csv_path_from_static = None ,
        )
    
@app.route('/download')
def download():
    directory = os.path.join(app.root_path, 'files') 
    return send_file(os.path.join(directory, csv_path), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)




