"""
This UI was created to display the original JSON output with better visibilty
Addresses copyright appropriately and displays the credited photographer for each image

Created on Feb 27, 2023

@author=avacrocker03 @email=acrocker2021@my.fit.edu
@author=tcarlson03 @email=tcarlson2021@my.fit.edu
"""

import json
import sys
import cv2
from ezgraphics import GraphicsImage, GraphicsWindow
import requests
from PIL import Image
import os
from datetime import datetime, timedelta
import collections
collections.Callable = collections.abc.Callable
import bs4
import urllib.request
import textwrap
import sys


# to run:
# curl -o curl.txt "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&date={yyyy-mm-dd}" & python APOD_ui.py

class ApodUI:

    def __init__(self):
        self._window_width = 1000  # setting up dimensions for UI
        self._window_height = 750
        self._window = None
        self._canvas = None
        self.ui_layout()

    def txt_to_json(self):
        with open("curl.txt") as file:  # opening txt file
            apod_string = file.read()

        apod_json = json.loads(apod_string, strict=False)  # loading txt file as JSON

        return apod_json

    def scrape_apod_data(self):
        json = self.txt_to_json()  # getting JSON file
        date = "ap" + json["date"].replace('-', "")[2:]
        site = urllib.request.urlopen(f"https://apod.nasa.gov/apod/{date}.html")  # url to NASA APOD website
        doc = bs4.BeautifulSoup(site, 'html.parser')  # parsing site to scrape
        return doc

    def get_apod_data(self):
        doc = self.scrape_apod_data()
        b_list = []
        link_list = []
        data = []
        apod_json = self.txt_to_json()

        search = doc.find_all('a')
        for link in search:  # searching url for all 'a' tags
            link_list.append(link.text)

        search = doc.find_all('b')
        for b in search:  # searching url for all'b' tags
            b_list.append(b.get_text())

        try:
            index = link_list.index("<")
            tmrw_name = link_list[index - 1]
        except:
            tmrw_name = "N/A"
        
        tmrw_title = "Tomorrow's picture: "
        tmrw_img = tmrw_title + tmrw_name

        img_credit_title = "Image Credit & Copyright: "  # getting desired info from scraped lists
        if "copyright" in apod_json.keys():
            img_name = apod_json["copyright"]
        else:
            img_name = "NASA"
        img_credit = img_credit_title + img_name

        author_title = "Authors & Editors: "
        try: # trying to pull authors
            index = link_list.index(">")
            index2 = link_list.index("Specific rights apply")
            author_name = link_list[(index + 1): (index2 - 1)]
            authors = ""
            for name in author_name:  # concatenating authors into one string from list
                name = name.replace("\n","")
                authors = name + " " + authors
            authors2 = author_title + authors
        except:
            try: # trying to pull authors
                index = link_list.index("Educational Links")
                index2 = link_list.index("Point Communications")
                author_name = link_list[(index + 1): (index2 - 1)]
                authors = ""
                for name in author_name:
                    name = name.replace("\n","")
                    authors = name + " " + authors
                authors2 = author_title + authors
            except: # authors not found
                authors2 = "N/A"

        

        data.append(authors2)  # creates list of desired info
        data.append(tmrw_img)
        data.append(img_credit)
        return data

    def wrap_explanation(self):
        apod_json = self.txt_to_json()
        wrapper = textwrap.TextWrapper(width=140) # wrapping explanation to sceren
        wrap_list = wrapper.wrap(text=apod_json["explanation"])
        wrap_explanation = ""

        for val in wrap_list:
            wrap_explanation = wrap_explanation + val + "\n"

        return (wrap_explanation)

    def get_coords(self, text, x, y):
        coord = []
        text_obj = self._canvas.drawText(x, y, text) 
        bounding_box = self._canvas._tkcanvas.bbox(text_obj) # creating box around text
        text_w = bounding_box[2] - bounding_box[0]
        x = (self._window_width - text_w) / 2 # calculating center
        coord.append(x)
        text_h = bounding_box[3] - bounding_box[1]
        y = self._window_height - text_h # calculating center
        coord.append(y)
        self._canvas._tkcanvas.delete(text_obj)

        return coord

    def ui_layout(self):
        self._window_width = 1000  # setting up dimensions for UI
        self._window_height = 625
        apod_json = self.txt_to_json()
        # self._window_height = self.get_coords(self.wrap_explanation(),0,0)[1] + 50

        self._window = GraphicsWindow(self._window_width, self._window_height)  # initializing window
        try: # checking valid date
            self._window.setTitle("Astronomy Picture of the Day: " + apod_json["date"])  # setting window title
        except:
            print("Invalid Date")
            sys.exit()
        self._canvas = self._window.canvas()
        self._canvas.setBackground(192, 192, 192)

    def ui_display(self):
        data = self.get_apod_data()
        apod_json = self.txt_to_json()
        try:
            media_format = self.get_apod_image(apod_json["url"]) # checking if image is supported
        except:
            print("Unsupported Image Type")
            sys.exit()
        x = 0
        y = 0
        if media_format == "Not a valid number! Try again" or media_format == "Input must be a positive number":
            print(media_format)
            self.ui_display()
        if media_format[-3:] == 'gif' or media_format[-3:] == 'png':
            media_type = ""
            if media_format[-3:] == 'gif':
                media_type = 'Media Type: GIF Image'
            else:
                media_type = 'Media Type: PNG Image'
            pic = GraphicsImage(media_format)  # displaying APOD image
            pic_x = (self._window_width - pic.width()) / 2
            self.display_information()
            self._canvas.drawImage(pic_x, 100, pic)
            self._canvas.drawText(self.get_coords(self.wrap_explanation(), x, y)[0], pic.height() + 130,
                                  self.wrap_explanation())  # displaying APOD explanation

            self._canvas.drawText(self.get_coords(media_type, x, y)[0], pic.height() + 105, media_type)

        else:
            media_type = ''
            if media_format[-3:] == 'avi':
                media_type = 'Media Type: Video - Downloaded as image.avi'
            else:
                media_type = 'Media Type: JPG Image'
            self.display_information()
            self._canvas.drawText(self.get_coords(self.wrap_explanation(), x, y)[0], 250,
                                  self.wrap_explanation())  # displaying APOD explanation
            self._canvas.drawText(self.get_coords(media_type, x, y)[0], 215, media_type)

        self._window.wait()

    def display_information(self):  ## repeated in last function so created this one to call in both
        data = self.get_apod_data()
        apod_json = self.txt_to_json()
        x = 0
        y = 0
        self._canvas.setTextFont("times", "bold", 20)
        self._canvas.setTextJustify("center")
        self._canvas.drawText(self.get_coords(apod_json["title"], x, y)[0], 30, apod_json["title"])
        self._canvas.setTextFont("times", "normal", 12)
        self._canvas.drawText(self.get_coords(data[2], x, y)[0], 70, data[2])  # displaying img credit
        self._canvas.setTextFont("times", "bold", 10)
        bottom_text = self.update_time() + "  |  " + data[0] + "  |  " + data[1]
        self._canvas.drawText(self.get_coords(bottom_text, x, y)[0], 600, bottom_text)
        self._canvas.setTextFont("times", "bold", 11)


    def get_apod_image(self, url):
        response = requests.get(url)
        source_code = response.content
        filename = os.path.basename(url)  # scraping img for APOD display
        img_file = open(filename, "wb")
        img_file.write(source_code)


        scaled_width = 500  # scaling image
        scaled_height = 300
        img = Image.open(filename)
        media_int = (input("Choose media type: 1-PNG Image, 2- GIF Image, 3- Video, 4-Regular Form\n"))
        
        if media_int.isdigit():
            media_int = int(media_int)
        else:
            return "Input must be a positive number"
        
        if media_int == 1:  ## If user chooses PNG image
            media_type = 'PNG image'
            percent_width = (scaled_width / float(img.size[0]))
            percent_height = (scaled_height/float(img.size[1]))
            new_percent = min(percent_width, percent_height)
            new_w = int(img.size[0] * new_percent)
            new_h = int(img.size[1] * new_percent) # converting jpg to gif
            img = img.resize((new_w, new_h), Image.ANTIALIAS)
            img.save(filename + ".png")
            return filename + ".png"

        if media_int == 2:
            media_type = "GIF Image"
            percent_width = (scaled_width / float(img.size[0]))
            percent_height = (scaled_height/float(img.size[1]))
            new_percent = min(percent_width, percent_height)
            new_w = int(img.size[0] * new_percent)
            new_h = int(img.size[1] * new_percent) # converting jpg to gif
            img = img.resize((new_w, new_h), Image.ANTIALIAS)
            img.save(filename + ".gif")  # setting new filename
            return filename + ".gif"

        if media_int == 3:
            isclosed = 0
            while isclosed < 1000:
                # This is to check whether to break the first loop
                cap = cv2.VideoCapture('image.avi')
                while (True):
                    square, frame = cap.read()
                    # It should only show the frame when the ret is true
                    if square == True:
                        isclosed += 1
                        cv2.imshow('Video Image', frame)
                        if cv2.waitKey(1) == 27:
                            # When esc is pressed isclosed is 1
                            isclosed += 1
                            break
                    else:
                        break

            cap.release()
            cv2.destroyAllWindows()
            return 'image.avi'

        if media_int == 4:
            media_type = "Regular Form"
            img1 = cv2.imread(filename, cv2.IMREAD_ANYCOLOR)
            cv2.imshow("image", img1)
            cv2.waitKey(0)

            cv2.destroyAllWindows()  # destroy all windows
            return filename

        else:
            return "Not a valid number! Try again"

    
    def update_time(self):
        est_time = (datetime.utcnow() - timedelta(hours=4)).strftime('%H%M')  # Gets EST time
        current_time = datetime.now().strftime("%H%M")  # Gets time on computer
        difference = int(current_time) - int(est_time)  # Finds the hour difference between the two times
        if difference < 0:  # Finds time of computer when EST time is midnight
            difference = str("%04d" % difference)
            midnight = 2400 + int(difference)
            if midnight > 0:
                return self.tomorrow_image(midnight)
        else:
            midnight = str("%04d" % difference)
            return self.tomorrow_image(midnight)

    def tomorrow_image(self, midnight):
        date_time_obj = datetime.strptime(str(midnight), '%H%M') # getting midnight
        date_time = date_time_obj.strftime('%H:%M')
        new_time = "Tomorrow's image will be available at " + date_time
        return new_time


def main():
    apod_ui = ApodUI()
    apod_ui.ui_display()  # calling UI to display


main()