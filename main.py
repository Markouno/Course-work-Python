import time
import requests
from pprint import pprint
from access import vk_token # Токены
from tqdm import tqdm
import datetime
import json


class PartVK:
    def __init__(self, token, user_id, number):
        self.vk_token = token
        self.number = number
        self.ids = user_id

    def get_info(self):  # Получает ID в виде STR - возвращает ID в виде INT
        params = {
            'user_ids': self.ids,
            'access_token': vk_token,
            'v': '5.131'
        }
        response = requests.get(
            'https://api.vk.com/method/users.get', params=params)
        res = response.json()
        need_id = res['response'][0]['id']
        return need_id

    
    def get_photos(self): # Принимает ID - возвразщает json формат данных
        ids = self.get_info()
        params = {
            'owner_id': ids,
            'album_id': 'profile',
            'extended': '1',
            'access_token': vk_token,
            'v': '5.131',
            'count': self.number
        }
        response = requests.get(
            'https://api.vk.com/method/photos.get', params=params)
        res = response.json()
        return res['response']['items']
        

    def make_a_dict(self): # Функция получает json данные и перебирает их на составляющие, создавая словарь
        photos = self.get_photos()
        sizes_str = 'wzyrqpoxms'
        pics_dict = {}
        for photo in tqdm(photos, desc='Создаем словарь... '):
            time.sleep(0.5)
            likes = photo['likes']['count']  # Кол-во лайков
            timestamp = photo['date']  # Дата публикации в UNIX формате
            time_value = datetime.datetime.fromtimestamp(timestamp)
            time_post = time_value.strftime('%d-%m-%Y %H:%M:%S')
            if likes not in pics_dict:
                file_name = likes
            else:
                file_name = f"{likes}/{time_post}"

            max_size = 0
            for size in tqdm(photo["sizes"], desc='Обработка фотографии...'):
                time.sleep(0.5)
                counter = 9
                if size["height"] > 0:
                    if size["height"] > max_size:
                        pics_dict[file_name] = {'url':size['url'],'type':size['type']}
                        max_size = size["height"]
                else:
                    if sizes_str.index(size["type"]) < counter:
                        pics_dict[file_name] = {'url':size['url'],'type':size['type']}
                        counter = sizes_str.index(size["type"])
        return pics_dict


class YandexDisk:
    def __init__(self, token, photo_list, folder_name):
        self.ya_token = token
        self.photo_list = photo_list
        self.folder_name = folder_name

    def get_headers(self):  # Получаем хедерс для реквестов
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.ya_token)
        }

    def upload_file_to_disk(self):  # Загружаем файлы на ЯДиск
        '''
        Метод позволяет загружать фото на ЯДиск по URL

        '''
        href = 'https://cloud-api.yandex.net/v1/disk/resources/'
        method = 'upload'
        headers = self.get_headers()
        for path_file, url_link in tqdm(self.photo_list.items(), desc='Загружаем фото на облако... '):
            params = {'path': f"{self.folder_name}/{path_file}", 'url': url_link['url']}
            response = requests.post(f'{href}{method}/', params=params, headers=headers)
            response.raise_for_status()
            time.sleep(0.5)
        print()
        if response.status_code == 202:
            print("Фотографии успешно загружены!")
            print()
        else:
            print("Ошибка загрузки фотографий.")
            print()


    def create_folder(self):
        href = 'https://cloud-api.yandex.net/v1/disk/resources/'
        headers = self.get_headers()
        params = {'path': self.folder_name}
        response = requests.put(f'{href}', headers= headers, params= params)
        if response.status_code == 201:
            print('Папка создана')


    def _get_upload_link(self):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {"path": f'{self.folder_name}/Photos_dict', "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()


    def upload_json_to_disk(self):
        with open('data.json', 'w') as jsonfile:
            json.dump(self.photo_list, jsonfile)
        href = self._get_upload_link().get("href", "")
        response = requests.put(url= href, data=open('data.json', 'rb'))
        response.raise_for_status()
        if response.status_code == 201:
            print("Json-файл успешно загружен!")
        else:
            print("Ошибка загрузки Json-файла.")

    
if __name__ == "__main__":
    person_id = input('Введите ID или Никнейм пользователя: ')
    count_photo = int(input('Введите кол-во фотографий: '))
    ya_token = input('Введите Ваш токен от Яндекс Диска: ')
    folder_name = input('Введите имя папки: ')

    downloader_from_vk = PartVK(vk_token, person_id, count_photo)
    need_photo = downloader_from_vk.make_a_dict()
    
    
    uploader_to_yadisk = YandexDisk(ya_token, need_photo, folder_name)
    uploader_to_yadisk.create_folder()
    uploader_to_yadisk.upload_file_to_disk()
    uploader_to_yadisk.upload_json_to_disk()
