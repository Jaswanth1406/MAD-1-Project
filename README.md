# Household Services Application

## Project Overview
This is a multi-user application designed to provide comprehensive home servicing and solutions. It acts as a platform where customers can book various household services, service professionals can manage service requests, and admins can oversee and manage all platform activities.

## Frameworks Used
The project is built using the following frameworks:
- **Flask**: For backend application code.
- **Jinja2 Templates + Bootstrap**: For HTML generation and responsive styling.
- **SQLite**: For data storage.

**Note**: The entire application is designed to run locally for demonstration purposes.

---

## Roles and Responsibilities
The platform supports three distinct roles:

### 1. Admin (Superuser)
- **Access**: Root access, no registration required.
- **Responsibilities**:
  - Redirected to the admin dashboard upon login.
  - Monitor all users (customers and service professionals).
  - Create, update, and delete services with base prices.
  - Approve service professionals after verifying profile documents.
  - Block/unblock customers or service professionals based on fraudulent activity or poor reviews.
  - Search for professionals for review or action.

---

### 2. Service Professional
- **Access**: Login/registration required.
- **Responsibilities**:
  - Accept or reject assigned service requests.
  - Complete service requests and mark them as closed upon completion.
  - Profile attributes include:
    - ID, Name, Date Created, Description, Service Type, Experience, etc.
  - Professionals specialize in a single service type.
  - Profiles are visible to customers with customer reviews for reference.

---

### 3. Customer
- **Access**: Login/registration required.
- **Responsibilities**:
  - Search for services by name, location, or pin code.
  - Create, edit, or close service requests.
  - Post reviews and remarks on closed services.
  - View profiles of service professionals based on reviews and ratings.

---

## Key Terminologies

### **Service**
Represents a type of service offered, e.g., AC servicing, plumbing, etc.
- Attributes:
  - ID, Name, Price, Time Required, Description, etc.

### **Service Request**
Created by customers to request a service.
- Attributes:
  - `id`: Primary key
  - `service_id`: Foreign key (references services table)
  - `customer_id`: Foreign key (references customers table)
  - `professional_id`: Foreign key (references professionals table)
  - `date_of_request`
  - `date_of_completion`
  - `service_status` (requested/assigned/closed)
  - `remarks`

---

## Core Functionalities

### 1. Authentication
- Separate login/register forms for admin, service professionals, and customers.
- Forms include fields such as username and password.
- A model to differentiate between user types.

---

### 2. Admin Dashboard
- Redirected upon admin login.
- Manage customers and service professionals.
- Approve or block users based on activity and reviews.

---

### 3. Service Management
- Admin can:
  - Create new services with base prices.
  - Update existing services (name, price, time required, etc.).
  - Delete services.

---

### 4. Service Requests (Customer)
- Customers can:
  - Create service requests based on available services.
  - Edit requests (e.g., date of request, status, remarks).
  - Close completed requests.

---

### 5. Search Functionality
- **Customers**: Search for services by name, location, or pin code.
- **Admin**: Search for professionals to manage their status.

---

### 6. Service Actions (Professional)
- View all service requests.
- Accept or reject service requests.
- Mark services as completed after finishing.

---

## Application Wireframe
The application wireframe provides a visual guide for the app's workflow and navigation. While replication of the wireframe is not mandatory, it serves as a reference for the application's flow and user interface.

---



## Demo and Local Setup
1. Clone the repository.
2. Ensure you have Python, Flask, and SQLite installed.
3. Install dependencies using `pip install -r requirements.txt`.
4. Run the application using `flask run`.
5. Access the application at `http://localhost:5000`.

**Note**: All demo functionalities are designed to work on your local machine.

---

## Future Enhancements
- Implement advanced filtering for search functionality.
- Add analytics for admins to track platform performance.
- Integrate notifications for service requests and status updates.

---

## Contributing
Feel free to raise issues or contribute by submitting a pull request. For major changes, please open an issue to discuss what you would like to modify.

---

