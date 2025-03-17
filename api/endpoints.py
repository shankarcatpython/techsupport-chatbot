from flask import Blueprint, jsonify
import pandas as pd

api_blueprint = Blueprint('api', __name__)

df = pd.read_csv("data/incidents.csv")

@api_blueprint.route('/incidents', methods=['GET'])
def get_incidents():
    return jsonify(df.to_dict(orient="records"))
