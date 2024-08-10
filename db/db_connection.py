from pymongo import MongoClient
from flask import render_template
from pymongo.errors import ServerSelectionTimeoutError


def connect_to_database():
    # try :
    client = MongoClient('mongodb://mongo:27017/')
    db = client['mydatabase']
    return db
    # except ServerSelectionTimeoutError as e :
    #     raise Exception("Database connection failed. Ato jaigai vul val korte hbe na." + str(e))
