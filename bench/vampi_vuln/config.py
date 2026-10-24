import os
import connexion
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from connexion.exceptions import ProblemException
api_app = connexion.App(__name__, specification_dir='./openapi_specs')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(api_app.app.root_path, 'database/database.db')
api_app.app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
api_app.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
api_app.app.config['SECRET_KEY'] = 'random'
db = SQLAlchemy(api_app.app)

def custom_problem_handler(error):
    response = jsonify({'status': 'fail', 'message': getattr(error, 'detail', 'An error occurred')})
    response.status_code = error.status
    return response
api_app.add_error_handler(ProblemException, custom_problem_handler)
api_app.add_api('openapi3.yml')
