import time
import requests
from pprint import pprint
from access import vk_token, ya_token
from tqdm import tqdm
import webbrowser
import datetime

# Если есть возможность связаться с Вами в дискорде -  Merkiz#1121


class PartVK:
    def __init__(self, token):
        self.vk_token = token

    def get_info(self, ids):  # Получает ID в виде STR - возвращает ID в виде INT
        params = {
            'user_ids': ids,
            'access_token': vk_token,
            'v': '5.131'
        }
        response = requests.get(
            'https://api.vk.com/method/users.get', params=params)
        res = response.json()
        need_id = res['response'][0]['id']
        return need_id

    # Принимает ID - возвразщает словарь с мета-данными фото(дата, лайки, тип размера, ссылка)
    def get_photos(self, user_id, number):
        ids = self.get_info(user_id)
        params = {
            'owner_id': ids,
            'album_id': 'profile',
            'extended': '1',
            'access_token': vk_token,
            'v': '5.131',
            'count': number
        }
        response = requests.get(
            'https://api.vk.com/method/photos.get', params=params)
        res = response.json()
        pics = res['response']['items']
        pics_dict = {}
        pics_list = []
        count = 0

        for photo in tqdm(pics, desc='Получаем фотографии... '):
            time.sleep(0.5)
            count += 1
            photo_url = None  # Ссылка на источник
            likes = photo['likes']['count']  # Кол-во лайков
            timestamp = photo['date']  # Дата публикации в UNIX формате
            time_value = datetime.datetime.fromtimestamp(timestamp)
            time_post = time_value.strftime('%d-%m-%Y %H:%M:%S')

            for element in photo['sizes']:  # Перебор размеров
                if element['type'] == 'w':
                    photo_url = element['url']
                elif element['type'] == 'z':
                    photo_url = element['url']
                else:
                    photo_url = photo['sizes'][-1]['url']
                photo_type = element['type']  # Тип размера изображения

            pics_dict = {'likes': likes,
                         'date': time_post,
                         'url': photo_url,
                         'type_size': photo_type}
            pics_list.append(pics_dict)

        photo_list = {}
        for element in pics_list:
            if element['likes'] not in photo_list:
                photo_list.setdefault(
                    f"{element['likes']}.jpg", element['url'])
            else:
                photo_list.setdefault(
                    f"{element['likes']},{element['date']}.jpg", element['url'])
        return photo_list


class YandexDisk:
    def __init__(self, token):
        self.ya_token = token

    def get_headers(self):  # Получаем хедерс для реквестов
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.ya_token)
        }

    def upload_file_to_disk(self, photo_list, folder_name):  # Загружаем файлы на ЯДиск
        '''
        Метод позволяет загружать фото на ЯДиск по URL

        '''
        href = 'https://cloud-api.yandex.net/v1/disk/resources/'
        folder = folder_name
        method = 'upload'
        headers = self.get_headers()
        for path_file, url_link in tqdm(photo_list.items(), desc='Загружаем фото на облако... '):
            params = {'path': f"{folder_name}/{path_file}", 'url': url_link}
            response = requests.post(f'{href}{method}/', params=params, headers=headers)
            response.raise_for_status()
            time.sleep(0.5)
            if response.status_code == 202:
                webbrowser.open(
                    f"https://http.cat/{response.status_code}", new=2)

    def create_folder(self, folder_name):
        href = 'https://cloud-api.yandex.net/v1/disk/resources/'
        headers = self.get_headers()
        params = {'path': folder_name}
        response = requests.put(f'{href}', headers= headers, params= params)
        if response.status_code == 201:
            print('Папка создана')

    
if __name__ == "__main__":
    downloader_from_vk = PartVK(vk_token)
    uploader_to_yadisk = YandexDisk(ya_token)
    person_id = input('Введите ID пользователя: ')
    count_photo = int(input('Введите кол-во фотографий: '))
    folder_name = input('Введите имя папки: ')
    need_photo = downloader_from_vk.get_photos(person_id, count_photo)
    uploader_to_yadisk.create_folder(folder_name)
    uploader_to_yadisk.upload_file_to_disk(need_photo, folder_name)