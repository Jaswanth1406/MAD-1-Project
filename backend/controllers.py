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


admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/", methods=["GET", "POST"])
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
            return redirect(url_for('admin.admin_dashboard', admin_email=admin.email))
    
        flash("Invalid login credentials","danger")

    return render_template('login.html')



@admin_bp.route('/admin_dashboard')
@admin_bp.route('/admin_dashboard/<string:admin_email>' , methods=["GET", "POST"])
def admin_dashboard(admin_email=None):
    services = Service_Info.query.all()
    professional = Professional_Info.query.all()
    service_details = Service_Request.query.all()
    return render_template('adminhome.html', name=admin_email, service_info=services, professional_info=professional  , service_request=service_details)


@admin_bp.route('/addservice', methods=["GET", "POST"])
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
            
            return redirect(url_for('admin.admin_dashboard', admin_email=admin_email))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}")
    
    return render_template('addservice.html')


@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))

@admin_bp.route('/service/<int:id>/delete', methods=['POST', 'DELETE'])
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
            return redirect(url_for('admin.admin_dashboard', admin_email=admin_email))
        else:
            return redirect(url_for('admin.admin_dashboard'))  
    else:
        return f"Method {request.method} not allowed for this endpoint", 405
    
@admin_bp.route('/edit_service/<int:id>', methods=['POST'])
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
    
    
    return redirect(url_for('admin.admin_dashboard', admin_email=admin_email))

@admin_bp.route('/unblock_professional/<int:id>', methods=['POST'])
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
    
    if admin_email:
        return redirect(url_for('admin.admin_dashboard', admin_email=admin_email))
    else:
        return redirect(url_for('admin.admin_dashboard'))  

@admin_bp.route('/approve_professional/<int:id>', methods=['POST'])
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
    
    if admin_email:
        return redirect(url_for('admin.admin_dashboard', admin_email=admin_email))
    else:
        return redirect(url_for('admin.admin_dashboard'))  

@admin_bp.route('/reject_professional/<int:id>', methods=['POST'])
def reject_professional(id):
    admin_email = session.get('admin_email')
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
    
    if admin_email:
        return redirect(url_for('admin.admin_dashboard', admin_email=admin_email))
    else:
        return redirect(url_for('admin.admin_dashboard'))  

@admin_bp.route('/block_professional/<int:id>', methods=['POST'])
def block_professional(id):
    admin_email = session.get('admin_email')
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
    
    if admin_email:
        return redirect(url_for('admin.admin_dashboard', admin_email=admin_email))
    else:
        return redirect(url_for('admin.admin_dashboard'))  


@admin_bp.route('/admin_search')
@admin_bp.route('/admin_search/<string:session_email>')
def admin_search(session_email=None):
    session_email = session.get('admin_email')

    if not session_email:
        flash('You need to be logged in to access this page.', 'danger')
        return redirect(url_for('admin.login'))
    
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



@admin_bp.route('/professional_document/<int:id>', methods=['GET','POST']) 
def professional_document(id):
    admin_email = session.get('admin_email')  
    try:
        professional = Professional_Info.query.get(id)
        
        if not professional:
            flash("Professional not found.")
            return redirect(url_for('admin.admin_dashboard', email=admin_email)) 

        blob_data = professional.file_data
        mime_type = professional.file_mimetype
        
        if blob_data and mime_type:
            file_data = io.BytesIO(blob_data)
            return send_file(file_data, mimetype=mime_type) 
        else:
            flash("Document not found.","danger")
            return redirect(url_for('admin.admin_dashboard', email=admin_email))  

    except Exception as e:
        flash(f"An error occurred: {str(e)}","error")
        return redirect(url_for('admin.admin_dashboard', email=admin_email))  


@admin_bp.route('/admin_summary')
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
