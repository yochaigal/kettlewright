import app
import os

def app_static_path():
    app_path = app.__file__.replace('__init__.py','')
    return os.path.join(os.path.abspath(app_path), 'static')
    
    