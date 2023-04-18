import time
import requests
from pprint import pprint
from access import vk_token # Токены
from tqdm import tqdm
import datetime
import json
import sys


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
        if not res['response']:
            print('Пользователь не найден.')
            sys.exit()
        # pprint(res)
        # sys.exit()
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
        # pprint(res)
        # sys.exit()
        return res['response']['items']
        
    def make_a_dict(self): # Функция получает json данные и перебирает их на составляющие, создавая словарь
        photos = self.get_photos()
        pics_dict = {}
        for photo in tqdm(photos, desc='Создаем словарь... '):
            likes = photo['likes']['count']  # Кол-во лайков
            timestamp = photo['date']  # Дата публикации в UNIX формате
            time_value = datetime.datetime.fromtimestamp(timestamp)
            time_post = time_value.strftime('%d-%m-%Y %H:%M:%S') # Дата в обычном формате
            right_photo_size = sorted(photo['sizes'], key=lambda x: (x['width'], x['height']))[-1]
            url = right_photo_size['url']
            size_letter = right_photo_size['type']
            
            if likes in pics_dict:
                likes = f'{likes}_{time_post}'
                
            pics_dict[likes] = {'url': url, 'size': size_letter}
        # sys.exit()
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

    def __create_folder(self): # Приватный метод
        href = 'https://cloud-api.yandex.net/v1/disk/resources/'
        headers = self.get_headers()
        params = {'path': self.folder_name}
        response = requests.put(f'{href}', headers= headers, params= params)
        if response.status_code == 201:
            print('Папка создана')

    def upload_file_to_disk(self):  # Загружаем файлы на ЯДиск
        '''
        Метод позволяет загружать фото на ЯДиск по URL

        '''
        self.__create_folder()
        href = 'https://cloud-api.yandex.net/v1/disk/resources/'
        method = 'upload'
        headers = self.get_headers()
        json_list = []
        for title, value in tqdm(self.photo_list.items(), desc='Загружаем фото на облако... '):
            name = f'{title}.jpg'
            size = value['size']
            params = {'path': f"{self.folder_name}/{name}", 'url': value['url']}
            response = requests.post(f'{href}{method}/', params=params, headers=headers)
            response.raise_for_status()
            # time.sleep(0.3)
            json_list.append(
                {'file_name': name, 
                 'size': size}
            )
        with open('data.json', 'w') as jsonfile:
            for json_dict in json_list:
                json_str = json_dict
                json_object = json.loads(json_str)
                json.dump(json_object, jsonfile)
        
        if response.status_code == 202:
            print("Фотографии успешно загружены!")
            print()
        else:
            print("Ошибка загрузки фотографий.")
            print()



    # def make_a_json(self):
    #     with open('data.json', 'w') as jsonfile:
    #         json.dump(self.photo_list, jsonfile)
            
    #     data = {}

    #     for key, value in self.photo_list:

    
if __name__ == "__main__":
    person_id = input('Введите ID или Никнейм пользователя: ')
    count_photo = int(input('Введите кол-во фотографий: '))
    ya_token = input('Введите Ваш токен от Яндекс Диска: ')
    folder_name = input('Введите имя папки: ')

    downloader_from_vk = PartVK(vk_token, person_id, count_photo)
    need_photo = downloader_from_vk.make_a_dict()
    
    uploader_to_yadisk = YandexDisk(ya_token, need_photo, folder_name)
    uploader_to_yadisk.upload_file_to_disk()
