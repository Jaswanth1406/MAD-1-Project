from flask import Flask, render_template, request, flash, session , send_file , Blueprint
from flask import current_app as app
from flask import redirect, url_for
from backend.models import *
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime , date
from sqlalchemy import func , or_ , and_
from uuid import uuid4
import csv
from collections import Counter
import io

professional_bp = Blueprint('professional', __name__)

@app.route('/professionallogin', methods=["GET", "POST"])
def professionallogin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        experience = request.form.get('experience')
        service_id = request.form.get('service_name') 
        phone_number = request.form.get('phone_number')
        file = request.files.get('file_data')
        password_hash = generate_password_hash(password)

        file_data = None
        file_mimetype = None
        if file:
            file_data = file.read()
            file_mimetype = file.mimetype

        
        existing_user = Professional_Info.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!","warning")
            return render_template('service_professional_setup.html')

        
        selected_service = Service_Info.query.filter_by(id=service_id).first()

        if not selected_service:
            flash("Selected service is not valid!","info")
            return render_template('service_professional_setup.html')

        
        new_user = Professional_Info(
            email=email, 
            password=password_hash, 
            fullname=fullname,
            address=address, 
            pincode=pincode, 
            experience=experience, 
            service_name=selected_service.service_name,  
            phone_number=phone_number,
            file_data=file_data,
            file_mimetype=file_mimetype
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!","success")
            return render_template("login.html")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}")

    
    services = Service_Info.query.all()  
    return render_template('service_professional_setup.html', services=services)


@app.route('/professional_dashboard')
@app.route('/professional_dashboard/<string:professional_email>',  methods=["GET", "POST"])  
def professional_dashboard(professional_email=None):
    if not professional_email:
        professional_email = session.get('professional_email')  

    if not professional_email:
        flash('Please log in to continue.', 'warning')
        return redirect(url_for('login'))

 
    professional = Professional_Info.query.filter_by(email=professional_email).first()

    if not professional:
        flash('Professional not found!', 'danger')  
        return redirect(url_for('login'))


    today = date.today()


    service_requests = Service_Request.query.filter_by(professional_id=professional.id).filter(
        func.date(Service_Request.date_of_request) == today
    ).all()

    closed_services = ServiceRemarks.query.filter_by(professional_id=professional.id).all()

    services = Service_Info.query.all()  

    
    return render_template(
        'professionalhome.html', 
        name=professional_email, 
        service_info=services, 
        professional_info=professional, 
        service_requests=service_requests,
        closed_services=closed_services
    )


@app.route('/accept_service/<int:id>', methods=['POST'])
def approve_service(id):
    professional_email = session.get('professional_email')
    try:
        service_request = Service_Request.query.get(id)
        if service_request:
            service_request.service_status = 'Accepted'  
            db.session.commit()
            flash(f"Service has been approved!","success")
        else:
            flash("Service not found.","danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}","error")
    
    if professional_email:
        return redirect(url_for('professional_dashboard', professional_email=professional_email))
    else:
        return redirect(url_for('professional_dashboard'))  

@app.route('/reject_service/<int:id>', methods=['POST'])
def reject_service(id):
    professional_email = session.get('professional_email')
    try:
        service_request = Service_Request.query.get(id)
        if service_request:
            service_request.service_status = 'Rejected'  
            db.session.commit()
            flash("Service has been rejected!","info")
        else:
            flash("Service not found.","danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}","error")
    
    if professional_email:
        return redirect(url_for('professional_dashboard', professional_email=professional_email))
    else:
        return redirect(url_for('professional_dashboard')) 
    


@app.route('/edit_professional_profile', methods=['GET', 'POST'])
def professional_profile():
    session_email = session.get('professional_email')  
    if not session_email:
        flash('Please log in to continue.', 'warning')
        return redirect(url_for('login'))

    professional = Professional_Info.query.filter_by(email=session_email).first()  
    
    if not professional:
        flash('Professional not found', 'danger')
        return redirect(url_for('professional_dashboard', professional_email=session_email))
    
   
    selected_service = None
    
    if request.method == 'POST':
        email = request.form.get('email')
        cpassword = request.form.get('cpassword')
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        phone_number = request.form.get('phone_number')
        experience = request.form.get('experience')
        service_id = request.form.get('service_name')  
        file = request.files['file_data']

        file_data = None
        file_mimetype = None
        if file:
            file_data = file.read()
            file_mimetype = file.mimetype

        
        selected_service = Service_Info.query.filter_by(id=service_id).first()

        if not selected_service:
            flash("Selected service is not valid!","warning")
            return render_template('service_professional_setup.html')

        if not all([email, cpassword, password, fullname, address, pincode, phone_number]):
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('professional_profile'))

        if professional and check_password_hash(professional.password, cpassword):
            professional.email = email
            professional.password = generate_password_hash(password)
            professional.fullname = fullname
            professional.address = address
            professional.pincode = pincode
            professional.phone_number = phone_number
            professional.experience = experience
            professional.service_name = selected_service.service_name  
            professional.file_data = file_data
            professional.file_mimetype = file_mimetype

            try:
                db.session.commit()
                flash("Profile updated successfully!", "success")
                return redirect(url_for('professional_dashboard', professional_email=session_email))
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred while updating: {str(e)}", "danger")
        else:
            flash('Incorrect password.', 'danger')

    services = Service_Info.query.all() 
    return render_template('professionalprofile.html', professional=professional, services=services)


@app.route('/professional_search')
@app.route('/professional_search/<string:session_email>')
def professional_search(session_email=None):

    session_email = session.get('professional_email')
    

    if not session_email:
        flash('You need to be logged in to access this page.', 'danger')
        return redirect(url_for('login'))
    
    parameter = request.args.get('parameter')
    query = request.args.get('query')
    

    professional = Professional_Info.query.filter_by(email=session_email).first()
    

    if not professional:
        flash('Professional not found!', 'danger')
        return redirect(url_for('login'))
    
    professional_id = professional.id  
    service_remarks = []


    if parameter == 'Date':
        service_remarks = ServiceRemarks.query.filter(
            and_(
                ServiceRemarks.service_date.ilike(f'%{query}%'),
                ServiceRemarks.professional_id == professional_id  
            )
        ).all()
    
    elif parameter == 'Location':
        service_remarks = ServiceRemarks.query.join(Service_Request).join(Customer_Info).filter(
            and_(
                Customer_Info.address.ilike(f'%{query}%'),
                Service_Request.professional_id == professional_id  
            )
        ).all()

    elif parameter == 'Pin Code':
        service_remarks = ServiceRemarks.query.join(Service_Request).join(Customer_Info).filter(
            and_(
                Customer_Info.pincode.ilike(f'%{query}%'),
                Service_Request.professional_id == professional_id 
            )
        ).all()

    elif parameter == 'Ratings':
        service_remarks = ServiceRemarks.query.filter(
            and_(
                ServiceRemarks.rating.ilike(f'%{query}%'),
                ServiceRemarks.professional_id == professional_id  
            )
        ).all()


    return render_template(
        'professionalsearch.html',
        name=session_email,
        closed_services=service_remarks,
    )


@app.route('/export_csv_professional_closed_request')
def professional_export(session_email=None):
    session_email = session.get('professional_email')
    professional = Professional_Info.query.filter_by(email=session_email).first()

    if not professional:
        flash('Professional not found!', 'danger')  
        return redirect(url_for('login'))
    
    service_history = ServiceRemarks.query.filter_by(professional_id=professional.id).all()

    if not service_history:
        flash('No service history found!', 'danger')
        return redirect(url_for('professional_dashboard'))
    
    filename = uuid4().hex + '.csv'
    url = 'static/csv/' + filename
    with open(url, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Service Name', 'Service Date', 'Professional Name', 'Professional Contact',
            'Rating', 'Remarks', 'Customer Name', 'Customer Address', 'Customer Phone'
        ])
        for service in service_history:
            service_request = service.service_request_info 

            customer = service_request.customer

            writer.writerow([
                service.service_name,
                service.service_date,
                service.professional_name,
                service.professional_contact,
                service.rating,
                service.remarks,
                customer.fullname,          
                customer.address,
                customer.phone_number
            ])
    return redirect(url_for('static',filename='csv/'+filename))


@app.route('/professional_summary')
def professional_summary():
    session_email = session.get('professional_email')
    if not session_email:
        flash("Professional Not Logged In", "danger")
        return redirect(url_for('login'))
    
    professional = Professional_Info.query.filter_by(email=session_email).first()
    if not professional:
        flash("Professional Not Found", "danger")
    

    service_remarks = ServiceRemarks.query.filter_by(professional_id=professional.id).all()
    ratings = [service.rating for service in service_remarks]
    

    rating_counts = Counter(ratings)
    labels = list(rating_counts.keys())  
    data = list(rating_counts.values()) 

    service_request = Service_Request.query.filter_by(professional_id=professional.id).all()
    statuses = [service.service_status for service in service_request]
    

    status_counts = Counter(statuses)
    labels1 = list(status_counts.keys())
    data1 = list(status_counts.values())
    

    return render_template(
        'professionalsummary.html',
        name = session_email,
        labels = labels,  
        data = data,
        labels1 = labels1,
        data1 = data1
    )
