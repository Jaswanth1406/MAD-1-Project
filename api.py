from flask import jsonify, request
from backend.models import *
from flask_restful import Api, Resource, reqparse
from app import app




api = Api(app)

class ServiceResource(Resource):
    
    service_put_args = reqparse.RequestParser()
    service_put_args.add_argument("service_name", type=str, help="Service name is required", required=True)
    service_put_args.add_argument("service_description", type=str, help="Description is required", required=True)
    service_put_args.add_argument("service_price", type=int, help="Price is required", required=True)

    def get(self, id=None):
        if id:
            service = Service_Info.query.get(id)
            if not service:
                return {"message": "Service not found"}, 404
            return jsonify({
                "id": service.id, 
                "service_name": service.service_name, 
                "service_description": service.service_description,
                "service_price": service.service_price
            })
        

    def post(self):
        if not request.json or not 'service_name' in request.json:
            return {"message": "Missing required fields"}, 400

        try:
            new_service = Service_Info(
                service_name=request.json.get('service_name'),
                service_description=request.json.get('service_description', None),
                service_price=request.json.get('service_price', 0)
            )
            db.session.add(new_service)
            db.session.commit()
            return jsonify({"message": "Service created", "id": new_service.id}), 201
        except Exception as e:
            db.session.rollback()
            return {"message": f"Error creating service: {str(e)}"}, 500

    def put(self, id):
        service = Service_Info.query.get(id)
        if not service:
            return {"message": "Service not found"}, 404

        args = self.service_put_args.parse_args()  
        try:
            service.service_name = args['service_name']
            service.service_description = args['service_description']
            service.service_price = args['service_price']
            db.session.commit()
            return jsonify({"message": "Service updated", "id": service.id})
        except Exception as e:
            db.session.rollback()
            return {"message": f"Error updating service: {str(e)}"}, 500


    def delete(self, id):
        service = Service_Info.query.get(id)
        if not service:
            return {"message": "Service not found"}, 404

        try:
            db.session.delete(service)
            db.session.commit()
            return jsonify({"message": "Service deleted", "id": id})
        except Exception as e:
            db.session.rollback()
            return {"message": f"Error deleting service: {str(e)}"}, 500


api.add_resource(ServiceResource, '/services', methods=['POST'], endpoint="create_service")
api.add_resource(ServiceResource, '/services/<int:id>', methods=['GET', 'PUT', 'DELETE'], endpoint="manage_service")
