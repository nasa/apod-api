import requests
import os
from PIL import Image


class Data:
    
    def __init__(self, api_key):
        self.response = requests.get("https://api.nasa.gov/planetary/apod?api_key="+api_key).json()
    
    def get_date(self):
        date = self.response['date']
        return date
    
    def get_explaination(self):
        explaination = self.response['explanation']
        return explaination
    
    def get_hdurl(self):
        hdurl = self.response['hdurl']
        return hdurl
    
    def get_media_type(self):
        media_type = self.response['media_type']
        return media_type
    
    def get_service_version(self): 
        service_version = self.response['service_version']
        return service_version
    
    def get_title(self):
        service_version = self.response['title']
        return service_version
    
    def get_url(self):
        url = self.response['url']
        return url
    
    def download_image(url, date):
        if os.path.isfile(f'{date}.png') == False:
            raw_image = requests.get(url).content
            with open(f'{date}.jpg', 'wb') as file:
                file.write(raw_image)
        else:
            return FileExistsError
    
    def convert_image(image_path):
        path_to_image = os.path.normpath(image_path)
        basename = os.path.basename(path_to_image)
        filename_no_extension = basename.split(".")[0]
        base_directory = os.path.dirname(path_to_image)
        image = Image.open(path_to_image)
        image.save(f"{base_directory}/{filename_no_extension}.png")
