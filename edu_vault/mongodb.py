import certifi
from django.conf import settings
from pymongo import MongoClient


# TODO : add to personal documentation
class MongoDbConnectionManager:
    """
    Mongo connection manager to connect and safely close mongodb connections
    """

    def __init__(self):
        self.mongo_uri = getattr(settings, "MONGO_URL", "mongodb://localhost:27017")
        self.client = None

    def __enter__(self):
        self.client = MongoClient(self.mongo_uri, tlsCAFile=certifi.where())
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()


def get_collection(collection_name, db_name="defaultDatabase"):
    """
    :param collection_name:
    :param db_name:
    :return:
    """

    with MongoDbConnectionManager() as client:
        db = client.get_database(db_name)
        collection = db.get_collection(collection_name)
        return collection


def write_to_collection(collection_name, data, db_name="defaultDatabase"):
    pass
