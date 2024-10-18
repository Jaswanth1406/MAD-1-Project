from flask import Flask
from backend.models import *
import secrets
from flask_restful import Api

app = None

def init_app():
    A_Z_HouseHoldapp = Flask(__name__)
    A_Z_HouseHoldapp.debug = True
    A_Z_HouseHoldapp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///A_Z_HouseHold.db'
    A_Z_HouseHoldapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    A_Z_HouseHoldapp.secret_key = secrets.token_hex(16)
    
    db.init_app(A_Z_HouseHoldapp)
    with A_Z_HouseHoldapp.app_context(): 
        db.create_all()  
    return A_Z_HouseHoldapp

app = init_app()


from backend.customerroutes import customer_bp
from backend.professionalroutes import professional_bp
from backend.controllers import admin_bp


app.register_blueprint(customer_bp)
app.register_blueprint(professional_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=True)
