from flask import Flask, render_template, request, flash, session , send_file 
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


with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        
        customer = Customer_Info.query.filter_by(email=email).first()
        if customer and check_password_hash(customer.password, password) and customer.is_blocked == False:
            session['customer_email'] = email
            return redirect(url_for('customer_dashboard', customer_email=customer.email))

       
        professional = Professional_Info.query.filter_by(email=email).first()
        if professional and check_password_hash(professional.password, password):
            session['professional_email'] = email
            return redirect(url_for('professional_dashboard', professional_email=professional.email))

        
        admin = Admin_Info.query.filter_by(email=email).first()
        if admin:
            session['admin_email'] = email
            return redirect(url_for('admin_dashboard', admin_email=admin.email))
    
        flash("Invalid login credentials","danger")

    return render_template('login.html')


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

@app.route('/admin_dashboard')
@app.route('/admin_dashboard/<string:admin_email>' , methods=["GET", "POST"])
def admin_dashboard(admin_email=None):
    services = Service_Info.query.all()
    professional = Professional_Info.query.all()
    service_details = Service_Request.query.all()
    customer = Customer_Info.query.all()
    return render_template('adminhome.html', name=admin_email, service_info=services, professional_info=professional  , service_request=service_details,customer_info = customer)


@app.route('/addservice', methods=["GET", "POST"])
def addservice():
    if request.method == 'POST':
        servicename = request.form.get('servicename').strip()
        description = request.form.get('description')
        baseprice = request.form.get('baseprice')
       
        existing_service = Service_Info.query.filter_by(service_name=servicename).first()
        if existing_service:
            flash("Service already registered!","info")
            return render_template('addservice.html')
        
        new_service = Service_Info(service_name=servicename, service_description=description, service_price=baseprice)
        try:
            db.session.add(new_service)
            db.session.commit()
            flash("Service added successfully!","success")

            admin_email = session.get('admin_email')  
            
            return redirect(url_for('admin_dashboard', admin_email=admin_email))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}")
    
    return render_template('addservice.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/service/<int:id>/delete', methods=['POST', 'DELETE'])
def delete_service(id):
    admin_email = session.get('admin_email') 
    
    if request.method in ['POST', 'DELETE']:
        service = Service_Info.query.get_or_404(id)
        
        try:
            db.session.delete(service)
            db.session.commit()
            
            flash('Service deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting service!', 'error')
            print(f"Error deleting service: {str(e)}")
        
        if admin_email:
            return redirect(url_for('admin_dashboard', admin_email=admin_email))
        else:
            return redirect(url_for('admin_dashboard'))  
    else:
        return f"Method {request.method} not allowed for this endpoint", 405
    
@app.route('/edit_service/<int:id>', methods=['POST'])
def edit_service(id):
    admin_email = session.get('admin_email')
    if request.method == 'POST':
        servicename = request.form.get('servicename')
        description = request.form.get('description')
        baseprice = request.form.get('baseprice')
        
        service = Service_Info.query.get(id)
        
        if service:
            service.service_name = servicename
            service.service_description = description
            service.service_price = baseprice

            try:
                db.session.commit()
                flash("Service updated successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred while updating: {str(e)}", "danger")
        else:
            flash("Service not found.", "danger")
    
    
    return redirect(url_for('admin_dashboard', admin_email=admin_email))

@app.route('/unblock_professional/<int:id>', methods=['POST'])
def unblock_professional(id):
    admin_email = session.get('admin_email')
    try:
        professional = Professional_Info.query.get(id)
        if professional:
            professional.is_blocked = False 
            db.session.commit()
            flash(f"{professional.fullname} has been Unblocked!","primary")
        else:
            flash("Professional not found.","danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}","error")
    

    return redirect(url_for('admin_dashboard', admin_email=admin_email))


@app.route('/approve_professional/<int:id>', methods=['POST'])
def approve_professional(id):
    admin_email = session.get('admin_email')
    try:
        professional = Professional_Info.query.get(id)
        if professional:
            professional.status = 'Approved'  
            db.session.commit()
            flash(f"{professional.fullname} has been approved!","success")
        else:
            flash("Professional not found.","danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}","error")

    return redirect(url_for('admin_dashboard' , admin_email = admin_email))

@app.route('/reject_professional/<int:id>', methods=['POST'])
def reject_professional(id):
    admin_email = session.get('admin_email')
    if not admin_email:  
        flash("Admin email not found in session. Please log in again.", "warning")
        return redirect(url_for('login'))  
    try:
        professional = Professional_Info.query.get(id)
        if professional:
            professional.status = 'Rejected'  
            db.session.commit()
            flash(f"{professional.fullname} has been rejected!","success")
        else:
            flash("Professional not found.","danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}","error")
    
    return redirect(url_for('admin_dashboard', admin_email=admin_email))


@app.route('/block_professional/<int:id>', methods=['POST'])
def block_professional(id):
    admin_email = session.get('admin_email')
    if not admin_email:  
        flash("Admin email not found in session. Please log in again.", "warning")
        return redirect(url_for('login'))  
    try:
        professional = Professional_Info.query.get(id)
        if professional:
            professional.is_blocked = True  
            db.session.commit()
            flash(f"{professional.fullname} has been blocked!","success")
        else:
            flash("Professional not found.","danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}","error")
    
    return redirect(url_for('admin_dashboard', admin_email=admin_email))



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


@app.route('/admin_search')
@app.route('/admin_search/<string:session_email>')
def admin_search(session_email=None):
    session_email = session.get('admin_email')

    if not session_email:
        flash('You need to be logged in to access this page.', 'danger')
        return redirect(url_for('login'))
    
    parameter = request.args.get('parameter')
    query = request.args.get('query')

    
    services = []
    professionals = []
    service_details = []

    if parameter == 'Services':
                services = Service_Info.query.filter(or_(
                Service_Info.service_name.ilike(f'%{query}%'),
                Service_Info.service_price.ilike(f'%{query}%')
            )
        ).all()

    elif parameter == 'Professional':
                professionals = Professional_Info.query.filter(or_(
                Professional_Info.fullname.ilike(f'%{query}%'),
                Professional_Info.service_name.ilike(f'%{query}%'),
                Professional_Info.experience.ilike(f'%{query}%')
            )
        ).all()

    elif parameter == 'Service History':
        service_details = Service_Request.query.filter(
            or_(
                Service_Request.date_of_request.ilike(f'%{query}%'),
                Service_Info.service_name.ilike(f'%{query}%'),  
                Professional_Info.fullname.ilike(f'%{query}%'),  
                Service_Request.service_status.ilike(f'%{query}%')
            )
        ).join(Service_Info, Service_Request.service).join(Professional_Info, Service_Request.professional).all()



    return render_template(
        'adminsearch.html',
        name=session_email,
        service_info=services,
        professional_info=professionals,
        service_request=service_details
    )


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




@app.route('/professional_document/<int:id>', methods=['GET','POST']) 
def professional_document(id):
    admin_email = session.get('admin_email')  
    try:
        professional = Professional_Info.query.get(id)
        
        if not professional:
            flash("Professional not found.")
            return redirect(url_for('admin_dashboard', email=admin_email)) 

        blob_data = professional.file_data
        mime_type = professional.file_mimetype
        
        if blob_data and mime_type:
            file_data = io.BytesIO(blob_data)
            return send_file(file_data, mimetype=mime_type) 
        else:
            flash("Document not found.","danger")
            return redirect(url_for('admin_dashboard', email=admin_email))  

    except Exception as e:
        flash(f"An error occurred: {str(e)}","error")
        return redirect(url_for('admin_dashboard', email=admin_email))  


from collections import Counter

@app.route('/admin_summary')
def admin_summary():
    session_email = session.get('admin_email')
    

    service_remarks = ServiceRemarks.query.all()
    ratings = [service.rating for service in service_remarks]
    

    rating_counts = Counter(ratings)
    labels = list(rating_counts.keys())  
    data = list(rating_counts.values()) 

    service_request = Service_Request.query.all()
    statuses = [service.service_status for service in service_request]
    

    status_counts = Counter(statuses)
    labels1 = list(status_counts.keys())
    data1 = list(status_counts.values())
    

    return render_template(
        'adminsummary.html',
        name = session_email,
        labels = labels,  
        data = data,
        labels1 = labels1,
        data1 = data1
    )

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
@app.route('/unblock_customer/<int:id>', methods=['POST'])
def unblock_customer(id):
    admin_email = session.get('admin_email')
    
    if not admin_email:  
        flash("Admin email not found in session. Please log in again.", "warning")
        return redirect(url_for('login')) 

    try:
        customer = Customer_Info.query.get(id)
        if customer:
            customer.is_blocked = False 
            db.session.commit()
            flash(f"{customer.fullname} has been Unblocked!", "primary")
        else:
            flash("Customer not found.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")

    return redirect(url_for('admin_dashboard', admin_email=admin_email))


@app.route('/block_customer/<int:id>', methods=['POST'])
def block_customer(id):
    admin_email = session.get('admin_email')
    
    if not admin_email:  
        flash("Admin email not found in session. Please log in again.", "warning")
        return redirect(url_for('login'))  

    try:
        customer = Customer_Info.query.get(id)
        if customer:
            customer.is_blocked = True  
            db.session.commit()
            flash(f"{customer.fullname} has been blocked!", "success")
        else:
            flash("Customer not found.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "error")

    return redirect(url_for('admin_dashboard', admin_email=admin_email))
