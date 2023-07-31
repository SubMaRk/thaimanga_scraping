import requests as rq
from bs4 import BeautifulSoup as bs
import re
import os
import urllib.parse
from http.client import IncompleteRead
from requests.exceptions import Timeout, RequestException
import time
import subprocess
import hashlib
import threading
import concurrent.futures
import json

# UserAgent.
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}

clear = lambda: subprocess.call('cls||clear', shell=True)

# Set main URL and variations.
main_url = "https://www.thaimanga.net/manga-list"
show_url = "?show="
variations = ["."] + ["0-9"] + [chr(i) for i in range(ord("A"), ord("Z") + 1)]

# Create list folder to save manga list.
folder_list = "list"

# Function to scraping info and images for a manga URL.
def process_manga(manga_url):
    print(f"Connecting to {manga_url}...")
    rsp = rq.get(manga_url)
    soup = bs(rsp.content, "html.parser")

    # Get information of manga from main-info div.
    manga_info = soup.find("div", class_="main-info")

    # Get first chapter url.
    li_first_tag = soup.find('li', attrs={'data-num': '1'})
    if li_first_tag:
        chapter_url = li_first_tag.find('a')['href']
    else:
        chapter_url = ''

    # Get manga type example manga, manhua, manhwa and comic.
    manga_type = manga_info.find_all('div', class_='imptdt')
    if manga_type:
        manga_type = manga_type[1]
        category = manga_type.find('a').text.strip()
    else:
        category = ''

    # Get manga title and remove unnecessary charactor.
    manga_title = manga_info.find("h1", class_="entry-title")
    if manga_title:
        title = manga_title.text.strip()

    sanitized = re.sub(r'[\\/:"*?<>|]', '', title)

    # Get manga status example ongoing, end.
    manga_status = manga_info.find('div', class_='imptdt')
    if manga_status:
        status = manga_status.find('i').text.strip()
    else:
        status = ''

    # Get post date.
    post_date = manga_info.find("time", itemprop="datePublished")
    if post_date:
        post_time = post_date.get("datetime", "")

    # Get update date.
    last_update = manga_info.find("time", itemprop="dateModified")
    if last_update:
        update_time = last_update.get("datetime", "")


    # Create folder to save failed load url.
    fail_folder = "failed"
    if not os.path.exists(fail_folder):
        os.makedirs(fail_folder)

    # Create folder to save manga data.
    data_folder = "data"
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    # Parse url to readable and set as data file name.
    decoded_url = urllib.parse.urlparse(manga_url)
    manga_name = decoded_url.path.split("/")
    file_data_name = urllib.parse.unquote(manga_name[2])
    file_data_path = os.path.join(data_folder, f"{file_data_name}.txt")

    # Read failed url from exists file.
    fail_data_path = os.path.join(fail_folder, f"{file_data_name}.txt")
    if os.path.exists(fail_data_path):
        fail_urls = []
        print(f"Geting failed URL from : {fail_data_path}")
        with open(fail_data_path, "r", encoding='utf-8') as file:
            urls = file.readlines()
            fail_urls.extend(url.strip() for url in urls)
        print(f'Reading failed url from {fail_data_path} finish!')
    else:
        print(f"No failed url in this {manga_name}.")

    # Read information from data file if exists. if not, create new data file.
    old_type =''
    savestatus =''
    lastupdate =''
    type_prefix = "Type : "
    status_prefix = "Status : "
    lastvisit_prefix = "Last Visit : "
    lastupdate_prefix = "Last Update : "
    if os.path.exists(file_data_path):
        print(f"Reading file : {file_data_path}...")
        with open(file_data_path, "r", encoding='utf-8') as file:
            for line in file:
                if line.startswith(type_prefix):
                    old_type = line[len(type_prefix):].strip()
                elif line.startswith(status_prefix):
                    savestatus = line[len(status_prefix):].strip()
                elif line.startswith(lastvisit_prefix):
                    chapter_url = line[len(lastvisit_prefix):].strip()
                elif line.startswith(lastupdate_prefix):
                    lastupdate = line[len(lastupdate_prefix):].strip()
                else:
                    continue
        print(f'Reading data from {file_data_path} finish!')
    else:
        print(f"No manga data found. Writing the new data.")
        with open(file_data_path, "w", encoding='utf-8') as file:
            file.write(f"Title : {title}\n")
            file.write(f"Type : {category}\n")
            file.write(f"Status : {status}\n")
            file.write(f"Post Date : {post_time}\n")
            file.write(f"Last Update : {update_time}\n")
            file.write(f"URL : {manga_url}\n")
            file.write(f"Last Visit : {chapter_url}")

    # Update status.
    if savestatus != '' and savestatus != status:
        with open(file_data_path, "r", encoding='utf-8') as file:
                data = file.readlines()
                newline = []
                save_status = data[2].strip()
                new_status = f"Status : {status}"
                for word in data:
                    newline.append(word.replace(save_status, new_status))

                with open(file_data_path, "w", encoding='utf-8') as file:
                    for line in newline:
                        file.writelines(line)
    # Update last update date.
    if lastupdate != '' and lastupdate != update_time:
        with open(file_data_path, "r", encoding='utf-8') as file:
                data = file.readlines()
                newline = []
                last_update = data[4].strip()
                new_update = f"Last Update : {update_time}"
                for word in data:
                    newline.append(word.replace(last_update, new_update))

                with open(file_data_path, "w", encoding='utf-8') as file:
                    for line in newline:
                        file.writelines(line)

    # Create Manga Folder.
    if category != '' and status != '':
        folder_name = f"[{category}] {sanitized} [{status}]"
    elif category == '' and status != '':
        folder_name = f"{sanitized} [{status}]"
    elif status == '' and category != '':
        folder_name = f"[{category}] {sanitized}"
    else:
        folder_name = f"{sanitized}"
    print(f"Folder Name : {folder_name}")

    # Rename folder if changed.
    if os.path.exists(file_data_path):
        old_folder = ''
        if old_type != '' and savestatus != '':
            old_folder = f"[{old_type}] {sanitized} [{savestatus}]"
        elif old_type == '' and savestatus != '':
            old_folder = f"{sanitized} [{savestatus}]"
        elif savestatus == '' and old_folder != '':
            old_folder = f"[{old_type}] {sanitized}"
        else:
            old_folder = f"{sanitized}"
        print(f"Old folder name : {old_folder}")
        if old_folder and old_folder != '':
            if old_folder != folder_name:
                safe_rename(old_folder, folder_name)

    # Create folder if not exist.
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Get cover image url.
    cover_img = soup.select_one(".thumb img")
    if cover_img:
        cover = cover_img["src"]
    else:
        cover = ''

    # Download cover image.
    if cover:
        file_extension = os.path.splitext(cover)[1]
        cover_name = f"{sanitized}{file_extension}"
        cover_path = os.path.join(folder_name, cover_name)
        if os.path.exists(cover_path):
            print(f"File size Checking : {cover_name}...")
            compare_size(cover, cover_path)
        else:
            rsp = rq.get(cover, stream=True)
            if rsp.status_code == 200:
                with open(cover_path, "wb") as file:
                    for chunk in rsp.iter_content(1024):
                        file.write(chunk)
    # Loop for fetching images from chapter url.
    while chapter_url:
        print(f"Title : {title}\nType : {category}\nStatus : {status}\nPost Date : {post_time}\nLast Update : {update_time}\nURL : {manga_url}")
        print(f"Fetching : {chapter_url}")

        # Replace new chapter url if found new chapter.
        with open(file_data_path, "r", encoding='utf-8') as file:
            data = file.readlines()
            newline = []
            last_visit = data[6].strip()
            new_visit = f"Last Visit : {chapter_url}"
            for word in data:
                newline.append(word.replace(last_visit, new_visit))

            with open(file_data_path, "w", encoding='utf-8') as file:
                for line in newline:
                    file.writelines(line)
                    print(f"Replace last visit url to {line}.")
        
        # Soup chapter url.
        print(f"Connecting to {chapter_url}...")
        rsp = rq.get(chapter_url)
        soup = bs(rsp.content, "html.parser")

        # Set script detect regex.
        script_tag = soup.find("script", string=re.compile(r'ts_reader\.run'))
        
        if script_tag:
            # Extract the JSON-like text from the script tag.
            pattern = r'ts_reader\.run\((.+?)\);'
            match = re.search(pattern, script_tag.string)

            if match:
                # Load the JSON-like text as a Python dictionary.
                try:
                    data = json.loads(match.group(1))
                except json.JSONDecodeError as e:
                    print("Error parsing JSON:", e)
                else:
                    print("Found images from script.")
                    jsondata = data
            else:
                print("Script tag content not found.")
        else:
            print("Script tag not found.")
            os.makedirs(os.path.dirname(fail_data_path), exist_ok=True)
             # Write failed chapter url to file.
            with open(fail_data_path, "a+", encoding='utf-8') as file:
                file.write(f"{chapter_url}\n")
            break
        
        # Get number of chapter from chapter url.
        getNum = chapter_url.split("/")
        chapterNum = getNum[-2]
        chapter_id = '-'.join(filter(lambda x: x.isdigit(), chapterNum.split('-')[-2:]))
        print(f"Chapter Number : {chapter_id}")
        chapter_folder = f"Chapter-{chapter_id}"

        # Check if 'sources' list exists and is not empty
        if 'sources' in jsondata and len(jsondata['sources']) > 0:
            # Extract image links from the 'images' key.
            images_list = jsondata['sources'][0].get('images', [])
            
            for i, img_link in enumerate(images_list):
                print(f"{img_link}\n")
                file_extension = os.path.splitext(img_link)[1]
                image_file_name = f"Chapter-{chapter_id}_image_{i}{file_extension}"
                image_file_path = os.path.join(folder_name, chapter_folder, image_file_name)
                # Check and compare size if file exists on local.
                if os.path.exists(image_file_path):
                    print(f"File size Checking : {image_file_name}...")
                    compare_size(img_link, image_file_path)
                else:
                    # If not, try to start download image.
                    os.makedirs(os.path.dirname(image_file_path), exist_ok=True)
                    download_with_retry(img_link, image_file_path)
            
            # Checking number of file in folder.
            print(f"All image links Downloaded. Checking the number of files.")
            chapter_fd = os.path.join(folder_name, chapter_folder)
            chapter_img_list = [os.path.join(chapter_fd, f) for f in os.listdir(chapter_fd) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
            local_list_count = len(chapter_img_list)
            img_list_count = len(images_list)
            # Check number of files on local and chapter page
            if local_list_count != img_list_count:
                # If files count is not match, write chapter url to failed file.
                print(f"Number of files is not same.\nWriting {chapter_url} to {fail_data_path}.")
                os.makedirs(os.path.dirname(fail_data_path), exist_ok=True)
                with open(fail_data_path, "a+", encoding='utf-8') as file:
                    file.write(f"{chapter_url}\n")
            else:
                 print(f"Number of files is same, {local_list_count}/{img_list_count} files.")

        else:
            # If images not found, write failed chapter url to failed file.
            print("No image found.")
            os.makedirs(os.path.dirname(fail_data_path), exist_ok=True)
            with open(fail_data_path, "a+", encoding='utf-8') as file:
                file.write(f"{chapter_url}\n")
            break
        
        # Set next chapter url from 'nextUrl' key.
        nextURL = jsondata['nextUrl']
        if nextURL != '':
            chapter_url = nextURL
            print(f"Next Chpter URL : {chapter_url}")
        else:
            break

        clear()
# Function safe rename manga folder.
def safe_rename(old_folder_name, new_folder_name):
    try:
        os.rename(old_folder_name, new_folder_name)
        print(f"Renamed {old_folder_name} to {new_folder_name}")
    except OSError as e:
        print(f"Error renaming {old_folder_name} to {new_folder_name}: {e}")

# Function to get content size from url.
def get_content_size(url):
    try:
        response = rq.head(url)
        if response.status_code == 200:
            content_size = int(response.headers.get('Content-Length', 0))
            return content_size
        else:
            print(f"Failed to retrieve content size. Status code: {response.status_code}")
    except rq.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    return None

# Function to compare between local file and remote file.
def compare_size(img_link, image_file_path):
    content_size = get_content_size(img_link)
    if content_size is not None:
        image_file_size = os.path.getsize(image_file_path)
        if image_file_size == content_size:
            print("Image file size and content size match.")
        else:
            print("Image file size and content size do not match.")
            print(f"Image file size: {image_file_size} bytes")
            print(f"Content size: {content_size} bytes")
            download_with_retry(img_link, image_file_path)
    else:
        print("Failed to get content size from the URL.")

# Function to download image with retry if error.
def download_with_retry(url, destination, timeout=5, max_retries=3):
    for i in range(max_retries):
        try:
            response = rq.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            with open(destination, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            compare_size(url, destination)
            break
        except (rq.exceptions.ChunkedEncodingError, IncompleteRead, rq.exceptions.RequestException) as e:
            print(f"Error downloading {url}. Retry {i + 1}/{max_retries}")
            # Wait for a short time before retrying (e.g., 1 second)
            time.sleep(1)
        except rq.exceptions.Timeout as e:
            print(f"Timeout error downloading {url}. Retry {i + 1}/{max_retries}")
            # Wait for a longer time before retrying (e.g., 5 seconds)
            break
        except Exception as e:
            break
    else:
        print(f"Failed to download {url} after {max_retries} retries.")

# Create a lock to avoid multiple threads writing to the same file at the same time
file_lock = threading.Lock()

# Function to create each manga url thread for processing.
def process_manga_thread(manga_url):
    try:
        process_manga(manga_url)
    except Exception as e:
        print(f"Error processing manga URL {manga_url}: {e}")

# Scraping manga urls from list page and save them to file each variations. 
manga_url = []
for variation in variations:
    list_name = f"{variation}.txt"
    list_path = os.path.join(folder_list, list_name)

    # Read from save file if exists.
    if os.path.exists(list_path):
        with open(list_path, "r", encoding='utf-8') as file:
            urls = file.readlines()
            manga_url.extend(url.strip() for url in urls)
    else:
    # If not exists, fetching new url from manga list page and save them
        page_number = 1
        while True:
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
                unquote = urllib.parse.unquote(url)
                manga_url.append(unquote)
                print(unquote)
                
                # Save each url to variation file.
                list_name = f"{variation}.txt"
                list_path = os.path.join(folder_list, list_name)
                
                # If file exist, continue write to file.
                if os.path.exists(list_path):
                    with open(list_path, "a+", encoding='utf-8') as file:
                        file.write(f"{unquote}\n")
                else:
                # Create file and write them to file.
                    os.makedirs(os.path.dirname(list_path), exist_ok=True)
                    with open(list_path, "a+", encoding='utf-8') as file:
                        file.write(f"{unquote}\n")
                
            print(f"Save urls to file : {list_name} successful.")

            page_number += 1

# Create a ThreadPoolExecutor with 16 workers
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
    # List to store the submitted futures
    futures = []

    # Submit manga URLs for processing and store the futures
    for manga in manga_url:
        future = executor.submit(process_manga_thread, manga)
        futures.append(future)

    # Process futures as they complete
    for future in concurrent.futures.as_completed(futures):
        try:
            # Get the result of the completed future (if any)
            result = future.result()
            if result is not None:
                print(f"Thread completed successfully: {result}")
            else:
                print("Thread did not return any result.")
        except Exception as e:
            print(f"Error processing manga URL: {e}")
