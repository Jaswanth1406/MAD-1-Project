from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

class Customer_Info(db.Model):
    __tablename__ = 'customer_info'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    fullname = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    is_blocked = db.Column(db.Boolean, default=False)

    service_requests = db.relationship(
        'Service_Request', backref='customer_info', cascade='all, delete-orphan'
    )

class Professional_Info(db.Model):
    __tablename__ = 'professional_info'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    fullname = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    service_name = db.Column(db.String(120), db.ForeignKey('service_info.service_name', ondelete="CASCADE"), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=True)
    file_mimetype = db.Column(db.String(100))
    status = db.Column(db.String(50), default='Pending')
    is_blocked = db.Column(db.Boolean, default=False)
    average_rating = db.Column(db.Float, nullable=True)

    service_requests = db.relationship(
        'Service_Request', backref='professional_info', cascade="all, delete-orphan"
    )
    service_remarks = db.relationship(
        'ServiceRemarks', backref='professional_info', cascade="all, delete-orphan"
    )

class Service_Info(db.Model):
    __tablename__ = 'service_info'
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(120), unique=True, nullable=False)
    service_description = db.Column(db.String(300), nullable=False)
    service_price = db.Column(db.Integer, nullable=False)

    service_requests = db.relationship('Service_Request', backref='service_info', cascade="all, delete-orphan")
    professionals = db.relationship('Professional_Info', backref='service', cascade="all, delete-orphan")

class Admin_Info(db.Model):
    __tablename__ = 'admin_info'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Service_Request(db.Model):
    __tablename__ = 'service_request'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service_info.id', ondelete='CASCADE'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer_info.id', ondelete='CASCADE'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional_info.id', ondelete='CASCADE'), nullable=False)
    date_of_request = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_of_completion = db.Column(db.DateTime, nullable=True)
    service_status = db.Column(db.String(50), default='requested')  
    remarks = db.Column(db.String(300), nullable=True)

    service = db.relationship('Service_Info', backref='requests', lazy=True)
    customer = db.relationship('Customer_Info', backref='requests', lazy=True)
    professional = db.relationship('Professional_Info', backref='requests', lazy=True)
    service_remarks = db.relationship('ServiceRemarks', backref='service_request_info', cascade='all, delete-orphan')

class ServiceRemarks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service_request.id', ondelete='CASCADE'), nullable=False)
    service_name = db.Column(db.String(100), nullable=False)
    service_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    professional_id = db.Column(db.Integer, db.ForeignKey('professional_info.id', ondelete='CASCADE'), nullable=False)
    professional_name = db.Column(db.String(100), nullable=False)
    professional_contact = db.Column(db.String(15), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.Text)

    customer = db.relationship('Customer_Info', 
        secondary='service_request', 
        primaryjoin='ServiceRemarks.professional_id==Service_Request.professional_id',
        secondaryjoin='Service_Request.customer_id==Customer_Info.id',
        viewonly=True
    )