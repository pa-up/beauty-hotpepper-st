import streamlit as st
import os
import pandas as pd
import sys
import csv
import time
import base64
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


def df_to_csv_local_url(df: pd.DataFrame , output_csv_path: str = "output.csv"):
    """ データフレーム型の表をcsv形式でダウンロードできるURLを生成する関数 """
    # csvの生成＆ローカルディレクトリ上に保存（「path_or_buf」を指定したら、戻り値は「None」）
    df.to_csv(path_or_buf=output_csv_path, index=False, header=False, encoding='utf-8-sig')
    # ダウロードできるaタグを生成
    csv = df.to_csv(index=False, header=False, encoding='utf-8-sig')
    b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()  # some strings <-> bytes conversions necessary here
    csv_local_href = f'<a href="data:file/csv;base64,{b64}" download={output_csv_path}>CSVでダウンロード</a>'
    return csv_local_href



def scraping_beauty_hotpepper(
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
    for reserved_salons_type_element in reserved_salons_type_elements:
        reserved_salons_element_list = reserved_salons_type_element.find_elements(By.TAG_NAME, "li")
        for reserved_salon_element in reserved_salons_element_list:
            salon_name = reserved_salon_element.find_element(By.CSS_SELECTOR, "p.b").text
            salon_page_link = reserved_salon_element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            reserved_salons_list.append([salon_name , salon_page_link])

    driver.quit()

    return reserved_salons_list


def main():
    st.title("ホットペッパービューティー取得サイト")
    st.write("<p></p>", unsafe_allow_html=True)

    browse_visually_form = st.radio("ブラウジングの様子を目視しますか？", ("目視する", "目視しない"))

    if st.button("取得開始") and browse_visually_form:
        # ページにアクセス
        searched_url = "https://beauty.hotpepper.jp/"
        if browse_visually_form == "目視する":
            browse_visually = "yes"
        else:
            browse_visually = "no"
        driver = browser_setup(browse_visually)

        # スクレイピング開始
        driver.get(searched_url)
        user_id = "yuki0606papkon9690@gmail.com"
        password = "yukiPAPKON9690"
        to_csv_list: list = scraping_beauty_hotpepper(
            driver , user_id , password ,
        )

        df = pd.DataFrame(to_csv_list)
        output_csv_path = "media/output.csv"
        csv_local_href = df_to_csv_local_url(df, output_csv_path)
        st.write("<p></p>", unsafe_allow_html=True)
        st.markdown(csv_local_href , unsafe_allow_html=True)


if __name__ == '__main__':
    main()
