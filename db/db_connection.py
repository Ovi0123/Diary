from pymongo import MongoClient
from flask import render_template


def connect_to_database():
    client = MongoClient('mongodb://mongo-service:27017/')
    db = client['mydatabase']
    return db
