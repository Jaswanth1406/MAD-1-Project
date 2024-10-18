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

customer_bp = Blueprint('customer', __name__)

@app.route('/customerlogin', methods=["GET", "POST"])
def customerlogin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        phone_number = request.form.get('phone_number')

        
        existing_user = Customer_Info.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!","warning")
            return render_template('create_account.html')

        password_hash = generate_password_hash(password)
        
        new_user = Customer_Info(email=email, password=password_hash, fullname=fullname,
                                 address=address, pincode=pincode, phone_number=phone_number)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!","success")
            return render_template("login.html")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}")
    
    
    return render_template('create_account.html')


@app.route('/customer_dashboard')
@app.route('/customer_dashboard/<string:customer_email>' ,  methods=["GET", "POST"])
def customer_dashboard(customer_email=None):
    if not customer_email:
        customer_email = session.get('customer_email')

    customer = Customer_Info.query.filter_by(email=customer_email).first()

    if not customer:
        flash('Customer not found!', 'danger')
        return redirect(url_for('login'))

    service_requests = Service_Request.query.filter_by(customer_id=customer.id).all()

    services = Service_Info.query.all()  

    return render_template(
        'customerhome.html', 
        name=customer_email, 
        service_info=services, 
        customer_info=customer, 
        service_request=service_requests
    )


@app.route('/servicedetails/<int:id>', methods=["GET", "POST"])
def service_details(id):
    customer_email = session.get('customer_email')
    if not customer_email:
        flash('Please log in to continue.', 'warning')
        return redirect(url_for('login'))
    
    customer = Customer_Info.query.filter_by(email=customer_email).first()
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('login'))

    service = Service_Info.query.get(id)
    if not service:
        flash(f'Service with ID {id} not found!', 'danger')
        return redirect(url_for('customer_dashboard', name=customer_email))


    if not service.service_name:
        flash('Service name not available.', 'warning')
        return redirect(url_for('customer_dashboard', name=customer_email))
    
    service_requests = Service_Request.query.filter_by(customer_id=customer.id, service_id=service.id).all()

    professionals = Professional_Info.query.filter_by(service_name=service.service_name, is_blocked=False).all()

    if not professionals:
        flash('No professionals available for this service', 'warning')
        return redirect(url_for('customer_dashboard', name=customer_email))

    return render_template('service_details.html', service=service, service_requests=service_requests, name=customer_email, professionals=professionals)


@app.route('/book_service/<int:service_id>', methods=['GET', 'POST'])
def book_service(service_id):
    customer_email = session.get('customer_email')
    if not customer_email:
        flash('Please login to book a service', 'warning')
        return redirect(url_for('login'))

    customer = Customer_Info.query.filter_by(email=customer_email).first()
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('login'))

    service = Service_Info.query.get(service_id)
    if not service:
        flash(f'Service with ID {service_id} not found', 'danger')
        return redirect(url_for('customer_dashboard'))

    professionals = Professional_Info.query.filter_by(service_name=service.service_name, is_blocked=False, status = 'Approved').all()

    if not professionals:
        flash('No professionals available for this service', 'warning')
        return redirect(url_for('customer_dashboard'))

    if request.method == 'POST':
        selected_professional_id = request.form.get('professional_id')


        if not selected_professional_id:
            flash('Professional ID was not selected.', 'danger')
            return redirect(url_for('customer_dashboard'))


        selected_professional = Professional_Info.query.get(selected_professional_id)

        if not selected_professional:
            flash('Selected professional not found.', 'danger')
            return redirect(url_for('customer_dashboard'))


        new_request = Service_Request(
            service_id=service.id,
            customer_id=customer.id,
            professional_id=selected_professional.id,
            service_status='assigned',
            remarks="Service has been booked",
            date_of_request=datetime.now()
        )

        db.session.add(new_request)
        db.session.commit()

        flash(f'Service booked successfully! Assigned professional: {selected_professional.fullname}', 'success')
        return redirect(url_for('customer_dashboard', name=customer_email))

    return render_template('book_service.html', service=service, professionals=professionals)


@app.route('/service_remarks/<int:service_request_id>', methods=['GET', 'POST'])
def service_remarks(service_request_id):
    service_request = Service_Request.query.get(service_request_id)

    if not service_request:
        flash('Service request not found', 'danger')
        return redirect(url_for('customer_dashboard'))

    return render_template('serviceremarks.html', service_request=service_request)


def update_average_rating(professional_id):
    professional = Professional_Info.query.get(professional_id)
    if professional:  
        all_ratings = [remark.rating for remark in professional.service_remarks]
        
        if all_ratings:
            avg_rating = sum(all_ratings) / len(all_ratings)
            professional.average_rating = round(avg_rating, 2) 
        else:
            professional.average_rating = None
        
        db.session.commit()


@app.route('/add_service_remarks/<int:service_request_id>', methods=["POST"])
def add_service_remarks(service_request_id):
    session_email = session.get('customer_email')
    service_request = Service_Request.query.filter_by(id=service_request_id).first()

    if not service_request:
        flash('Service request not found.', 'danger')
        return redirect(url_for('customer_dashboard', email=session_email))


    if service_request.service_status != 'Accepted':
        flash('Service request must be in Accepted status to add remarks.', 'danger')
        return redirect(url_for('customer_dashboard', email=session_email))

    if service_request.service_status == 'Closed':
        flash('Service request is already closed; remarks cannot be added.', 'danger')
        return redirect(url_for('customer_dashboard', email=session_email))


    service_name = request.form.get('service_name')
    service_date = request.form.get('service_date')
    professional_id = request.form.get('professional_id')
    professional_name = request.form.get('professional_name')
    professional_contact = request.form.get('professional_contact')
    rating = request.form.get('rating')
    remarks = request.form.get('remarks', None)


    if not all([service_name, service_date, professional_id, professional_name, professional_contact, rating]):
        flash('All fields are required.', 'danger')
        return redirect(url_for('service_details', id=service_request.service_id))  


    try:
        service_date = datetime.strptime(service_date, '%d/%m/%Y')
    except ValueError:
        flash('Invalid date format. Please use dd/mm/yyyy.', 'danger')
        return redirect(url_for('service_details', id=service_request.service_id))  


    try:
        new_remark = ServiceRemarks(
            service_id=service_request_id,  
            service_name=service_name,
            service_date=service_date,
            professional_id=professional_id,
            professional_name=professional_name,
            professional_contact=professional_contact,
            rating=rating,
            remarks=remarks
        )


        service_request.date_of_completion = datetime.now()
        service_request.service_status = 'Closed'

        db.session.add(new_remark)
        db.session.commit()

        update_average_rating(professional_id)

        flash('Service remarks added successfully!', 'success')
        return redirect(url_for('customer_dashboard', name=session_email))  

    except Exception as e:
        db.session.rollback() 
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('service_details', id=service_request.service_id))
    


@app.route('/edit_customer_profile', methods=['GET', 'POST'])
def customer_profile():
    session_email = session.get('customer_email')  
    if not session_email:
        flash('Please log in to continue.', 'warning')
        return redirect(url_for('login'))

    customer = Customer_Info.query.filter_by(email=session_email).first()  
    
    if not customer:
        flash('Customer not found', 'danger')
        return redirect(url_for('customer_dashboard', customer_email=session_email))

    if request.method == 'POST':
        email = request.form.get('email')
        cpassword = request.form.get('cpassword')
        password = request.form.get('password')
        fullname = request.form.get('fullname')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        phone_number = request.form.get('phone_number')

        if not all([email, cpassword, password, fullname, address, pincode, phone_number]):
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('customer_profile'))

        if customer and check_password_hash(customer.password, cpassword):
            customer.email = email
            customer.password = generate_password_hash(password)
            customer.fullname = fullname
            customer.address = address
            customer.pincode = pincode
            customer.phone_number = phone_number

            try:
                db.session.commit()
                flash("Profile updated successfully!", "success")
                return redirect(url_for('customer_dashboard', customer_email=session_email))
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred while updating: {str(e)}", "danger")
        else:
            flash('Incorrect password.', 'danger')

    
    return render_template('customerprofile.html', customer=customer)
    
@app.route('/customer_search')
@app.route('/customer_search/<string:session_email>')
def customer_search(session_email=None):
    session_email = session.get('customer_email')
    parameter = request.args.get('parameter')
    query = request.args.get('query')


    service_remarks = []
    services = []
    professionals = []
    found_services = False

    if parameter == 'Services':
        found_services = True
        services = Service_Info.query.filter(or_(
            Service_Info.service_name.ilike(f'%{query}%'),
            Service_Info.service_price.ilike(f'%{query}%')
        )).all()
        

    elif parameter == 'Professional':
        professionals = Professional_Info.query.filter(or_(
            Professional_Info.fullname.ilike(f'%{query}%'),
            Professional_Info.service_name.ilike(f'%{query}%'),
            Professional_Info.experience.ilike(f'%{query}%')
        )).all()

        if professionals:
            services = Service_Info.query.filter(
                Service_Info.service_name.in_([prof.service_name for prof in professionals])
            ).all()

    elif parameter == 'Location':
        service_remarks = Professional_Info.query.filter(
            Professional_Info.address.ilike(f'%{query}%')
        ).all()
        if service_remarks:
            services = Service_Info.query.filter(
                Service_Info.service_name.in_([sr.service_name for sr in service_remarks])
            ).all()

    elif parameter == 'Pin Code':
        service_remarks = Professional_Info.query.filter(
            Professional_Info.pincode.ilike(f'%{query}%')
        ).all()
        if service_remarks:
            services = Service_Info.query.filter(
                Service_Info.service_name.in_([sr.service_name for sr in service_remarks])
            ).all()

    return render_template(
        'customersearch.html',
        name=session_email,
        closed_services=service_remarks,
        service_info=services,
        professional_info=professionals,
        service=services[0] if services else None,
        found_services = found_services
    )


@app.route('/export_csv_customer_closed_request')
def customer_export(session_email=None):
    session_email = session.get('customer_email')
    customer = Customer_Info.query.filter_by(email=session_email).first()

    if not customer:
        flash('Customer not found!', 'danger')  
        return redirect(url_for('login'))
    

    service_history = ServiceRemarks.query.join(Service_Request).filter(Service_Request.customer_id == customer.id).all()

    if not service_history:
        flash('No service history found!', 'danger')
        return redirect(url_for('customer_dashboard'))
    
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
    
    return redirect(url_for('static', filename='csv/' + filename))


@app.route('/customer_summary')
def customer_summary():
    session_email = session.get('customer_email')
    if not session_email:
        flash("Customer Not Logged In", "danger")
        return redirect(url_for('login'))

    customer = Customer_Info.query.filter_by(email=session_email).first()
    if not customer:
        flash("Customer Not Found", "danger")


    service_request = Service_Request.query.filter_by(customer_id=customer.id).all()


    statuses = [service.service_status for service in service_request]
    status_counts = Counter(statuses)
    labels = list(status_counts.keys())
    data = list(status_counts.values())

    return render_template(
        'customersummary.html',
        name=session_email,
        labels=labels,  
        data=data,
    )


