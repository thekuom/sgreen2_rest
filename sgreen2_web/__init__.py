from pyramid.config import Configurator

try:
    # for python 2
    from urlparse import urlparse
except ImportError:
    # for python 3
    from urllib.parse import urlparse

from gridfs import GridFS
from pymongo import MongoClient


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    # MongoDB and Pyramid

    db_url = settings['mongo_uri']
    config.registry.db = MongoClient(db_url)

    def add_db(request):
        return config.registry.db.greenhouse

    def add_fs(request):
        return GridFS(request.db)

    config.add_request_method(add_db, 'db', reify=True)
    config.add_request_method(add_fs, 'fs', reify=True)

    # Routes
    config.add_route('home', '/')

    config.add_route('data_readings', '/data_readings')

    config.add_route('settings', '/settings')

    config.add_route('actuators', '/actuators')
    config.add_route('actuators_state', '/actuators/{name}/state')

    config.add_route('greenhouse_server_state', '/greenhouse_server_state')

    config.scan('sgreen2_web.views')

    from wsgicors import CORS
    return CORS(config.make_wsgi_app(), headers="*", methods="*", maxage="180", origin="*")
