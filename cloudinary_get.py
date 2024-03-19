import os

import cloudinary
# Import the cloudinary.api for managing assets
import cloudinary.api
# Import the cloudinary.uploader for uploading assets
import cloudinary.uploader
import requests

cloudinary.config(
    cloud_name="duom1fowc",
    api_key="567288744623174",
    api_secret="dw6rZN4rEZLcRLucrt-cijBhdv4",
    secure=True,
)

folder_name = "cards_new"
local_folder_path = "cards_1"

if not os.path.exists(local_folder_path):
    os.makedirs(local_folder_path)


def download_image(image_url, local_path):
    """Скачивает изображение по URL и сохраняет его в локальной файловой системе."""
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)


def fetch_and_download_images(folder_name, local_folder_path):
    """Извлекает изображения из Cloudinary и скачивает их локально, пропуская существующие."""
    next_cursor = None
    total_downloaded = 0
    total_skipped = 0

    while True:
        response = cloudinary.api.resources(
            type='upload',
            prefix=folder_name,
            max_results=500,
            next_cursor=next_cursor
        )

        for image in response['resources']:
            public_id = image['public_id']
            url = image['url']
            filename = public_id.split('/')[-1] + '.' + url.split('.')[-1]
            local_path = os.path.join(local_folder_path, filename)

            # Проверяем, существует ли файл уже
            if os.path.exists(local_path):
                print(f"Skipping existing file: {filename}")
                total_skipped += 1
                continue  # Пропускаем скачивание этого файла

            download_image(url, local_path)
            total_downloaded += 1
            print(f"Downloaded {total_downloaded}: {filename}")

        next_cursor = response.get('next_cursor')
        if not next_cursor:
            break

    print(f"Total images downloaded: {total_downloaded}")
    print(f"Total images skipped: {total_skipped}")



# Выполнение скачивания
fetch_and_download_images(folder_name, local_folder_path)
