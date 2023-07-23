import requests as rq
from bs4 import BeautifulSoup as bs
import re
import os
import urllib.parse
from http.client import IncompleteRead
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import subprocess

# UserAgent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}

clear = lambda: subprocess.call('cls||clear', shell=True)

# Set main URL
main_url = "https://www.thaimanga.net/manga-list/"
show_url = "?show="
variations = ["."] + ["0-9"] + [chr(i) for i in range(ord("A"), ord("Z") + 1)]

def download_with_retry(url, destination):
    max_retries = 5
    for i in range(max_retries):
        try:
            response = rq.get(url, stream=True)
            response.raise_for_status()
            with open(destination, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Download : {url} successful!")
            break
        except (rq.exceptions.ChunkedEncodingError, IncompleteRead, rq.exceptions.RequestException) as e:
            print(f"Error downloading {url}. Retry {i + 1}/{max_retries}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            break
    else:
        print(f"Failed to download {url} after {max_retries} retries.")

for variation in variations:
    page_number = 1
    while True:
        manga_url = []
        page_url = f"{main_url}/page/{page_number}/{show_url}{variation}"
        print(f"Fetching list from {page_url}")

        response = rq.get(page_url, headers=headers)
        soup = bs(response.content, 'html.parser')
        manga_list = soup.select('.bs .bsx')
        if not manga_list:
            page_number = 0
            break

        for data in manga_list:
            url = data.find('a')['href']
            manga_url.append(url)

        for manga in manga_url:
            url = f"{manga}"
            rsp = rq.get(url)
            soup = bs(rsp.content, "html.parser")
            manga_info = soup.find("div", class_="main-info")

            manga_type = manga_info.find_all('div', class_='imptdt')
            if manga_type:
                manga_type = manga_type[1]
                category = manga_type.find('a').text.strip()
            else:
                category = ''

            manga_title = manga_info.find("h1", class_="entry-title")
            if manga_title:
                title = manga_title.text.strip()

            # Create Manga Folder
            sanitized = re.sub(r'[\\/:"*?<>|]', '', title)
            if category != '':
                folder_name = f"[{category}] {sanitized}"
            else:
                folder_name = f"{sanitized}"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            post_date = manga_info.find("time", itemprop="datePublished")
            if post_date:
                post_time = post_date.get("datetime", "")

            last_update = manga_info.find("time", itemprop="dateModified")
            if last_update:
                update_time = last_update.get("datetime", "")

            cover_img = soup.select_one(".thumb img")
            if cover_img:
                cover = cover_img["src"]
            else:
                cover = ''
            if cover:
                file_extension = os.path.splitext(cover)[1]
                cover_name = f"{sanitized}.{file_extension}"
                cover_path = os.path.join(folder_name, cover_name)
                if os.path.exists(cover_path):
                    print(f"Skipping : {cover_name} (already exists)")
                else:
                    rsp = rq.get(cover, stream=True)
                    if rsp.status_code == 200:
                        with open(cover_path, "wb") as file:
                            for chunk in rsp.iter_content(1024):
                                file.write(chunk)

            li_first_tag = soup.find('li', attrs={'data-num': '1'})
            if li_first_tag:
                chapter_url = li_first_tag.find('a')['href']

            # Save manga data
            data_folder = "data"
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)

            decoded_url = urllib.parse.urlparse(manga)
            manga_name = decoded_url.path.split("/")
            file_data_name = urllib.parse.unquote(manga_name[2])
            file_data_path = os.path.join(data_folder, f"{file_data_name}.txt")
            target_prefix = "Last Visit : "
            if os.path.exists(file_data_path):
                with open(file_data_path, "r", encoding='utf-8') as file:
                    for line in file:
                        if line.startswith(target_prefix):
                            chapter_url = line[len(target_prefix):].strip()
            else:
                print(f"No manga data found. Writing the new data.")
                with open(file_data_path, "w", encoding='utf-8') as file:
                    file.write(f"Title : {title}\n")
                    file.write(f"Type : {category}\n")
                    file.write(f"Post Date : {post_time}\n")
                    file.write(f"Last Update : {update_time}\n")
                    file.write(f"URL : {manga}\n")
                    file.write(f"Last Visit : {chapter_url}")

            while chapter_url:
                print(f"Title : {title}\nType : {category}\nPost Date : {post_time}\nLast Update : {update_time}\nURL : {manga_url}")
                print(f"Fetching : {chapter_url}")
                chrome_options = Options()
                chrome_options.add_argument("--non-headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                driver = webdriver.Chrome(options=chrome_options)
                action = webdriver.ActionChains(driver)

                getNum = chapter_url.split("/")
                chapterNum = getNum[-2]
                chapter_id = '-'.join(filter(lambda x: x.isdigit(), chapterNum.split('-')[-2:]))
                print(f"Chapter Number : {chapterNum}\nChapter ID : {chapter_id}")
                chapter_folder = f"Chapter-{chapter_id}"

                try:
                    driver.get(chapter_url)
                    time.sleep(3)
                    driver.execute_script("window.scrollBy(0, 500);")
                    action.move_by_offset(0, 20)
                    action.perform()
                    time.sleep(3)
                    page_source = driver.page_source
                    soup = bs(page_source, "html.parser")
                    image_container = soup.select_one("#readerarea")
                    button = soup.select_one(".ctop")
                    if image_container:
                        image_tags = image_container.find_all("img")
                        if not image_tags:
                            print("No image found.")
                            break

                        for i, image_tag in enumerate(image_tags):
                            image_url = image_tag["src"]
                            print(image_url)
                            file_extension = os.path.splitext(image_url)[1]
                            image_file_name = f"Chapter-{chapter_id}_image_{i}{file_extension}"
                            image_file_path = os.path.join(folder_name, chapter_folder, image_file_name)
                            if os.path.exists(image_file_path):
                                print(f"Skipping : {image_file_name} (already exists)")
                            else:
                                os.makedirs(os.path.dirname(image_file_path), exist_ok=True)
                                # Use the download_with_retry function
                                download_with_retry(image_url, image_file_path)

                    next_chapter_link = button.find("a", class_="ch-next-btn")
                    if next_chapter_link and "disabled" not in next_chapter_link.get("class", []):
                        chapter_url = next_chapter_link["href"]
                    else:
                        break

                finally:
                    driver.quit()
                with open(file_data_path, "r", encoding='utf-8') as file:
                    data = file.readlines()
                    newline = []
                    last_update = data[5].strip()
                    new = f"Last Visit : {chapter_url}"
                    for word in data:
                        newline.append(word.replace(last_update, new))

                    with open(file_data_path, "w", encoding='utf-8') as file:
                        for line in newline:
                            file.writelines(line)
                clear()

        page_number += 1
