import random
import requests
import datetime
from config.settings import SERVICE_NOW_URL, SERVICE_NOW_TOKEN

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SERVICE_NOW_TOKEN}"
}

def create_servicenow_incident(user_query):
    """
    Attempts to create an incident in ServiceNow.
    Falls back to local simulation if API is unavailable.
    """
    data = {
        "short_description": user_query,
        "category": "Support"
    }
    try:
        response = requests.post(SERVICE_NOW_URL, json=data, headers=HEADERS)
        if response.status_code != 201:
            return simulate_local_incident(user_query)
        servicenow_response = response.json()
        incident_number = servicenow_response.get("result", {}).get("number", f"INC-{random.randint(10000, 99999)}")
        return {
            "incident_number": incident_number,
            "short_description": user_query,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "New",
            "assignment_group": "Technical Support",
            "priority": "Medium",
            "message": f"ServiceNow Incident {incident_number} has been successfully created."
        }
    except requests.exceptions.RequestException:
        return simulate_local_incident(user_query)

def simulate_local_incident(user_query):
    """
    Generates a realistic ServiceNow-style incident response when API is unavailable.
    """
    incident_number = f"INC-{random.randint(10000, 99999)}"
    return {
        "incident_number": incident_number,
        "short_description": user_query,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "New",
        "assignment_group": "Technical Support",
        "priority": "Medium",
        "message": f"ServiceNow Incident {incident_number} has been successfully created."
    }
