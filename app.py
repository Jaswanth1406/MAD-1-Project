from flask import Flask, jsonify, request
from backend.models import *
import secrets
from flask_restful import Api, Resource, reqparse


app = None

def init_app():
    A_Z_HouseHoldapp = Flask(__name__)
    A_Z_HouseHoldapp.debug = True
    A_Z_HouseHoldapp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///A_Z_HouseHold.db'
    A_Z_HouseHoldapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    A_Z_HouseHoldapp.secret_key = secrets.token_hex(16)
    A_Z_HouseHoldapp.app_context().push()
    db.init_app(A_Z_HouseHoldapp)
    return A_Z_HouseHoldapp

app = init_app()
from api import *
from backend.controllers import *


if __name__ == '__main__':
    app.run(debug=True)