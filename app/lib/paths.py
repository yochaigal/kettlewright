import app
import os
from flask import url_for
from urllib.request import urlopen

def app_static_path():
    app_path = app.__file__.replace('__init__.py','')
    return os.path.join(os.path.abspath(app_path), 'static')
    

def character_portrait_link(character):
    if character.custom_image == False:
        portrait_src = url_for('static', filename='images/portraits/' + character.image_url)
    elif character.image_url != None:
        portrait_src = character.image_url
    else:
        portrait_src = "/static/images/portraits/default-portrait.webp"
    return portrait_src

def is_url_image(image_url):
   try: 
       image_formats = ("image/png", "image/jpeg", "image/jpg","image/svg","image/webp","image/gif")
       site = urlopen(image_url)
       meta = site.info()
       if meta["content-type"] in image_formats:
           return True
       return False
   except:
       return True # some url throw exception even when they have an image


