from flask import Flask, request, render_template, jsonify
import pandas as pd
import random
from api.endpoints import api_blueprint
from services.langchain_service import analyze_incident, assess_technical_debt, validate_resolution_externally
from services.servicenow_api import create_servicenow_incident, TECHNICAL_KEYWORDS_SN
from fuzzywuzzy import process

app = Flask(__name__, template_folder="templates", static_folder="static")
app.register_blueprint(api_blueprint)

df = pd.read_csv("data/incidents.csv")

# Common responses for out-of-domain queries
OUT_OF_DOMAIN_RESPONSES = [
    "This query seems to be out of our domain knowledge." ,
    "Out of our Health care domain knowledge."
]

# ✅ List of known technical keywords to improve matching
TECHNICAL_KEYWORDS = TECHNICAL_KEYWORDS_SN


@app.route('/')
def home():
    return render_template("index.html")

@app.route('/ask', methods=['POST'])
def ask_llm():
    user_query = request.form.get("query", "").strip().lower()  # Normalize input

    if not user_query:
        return jsonify({"error": "Query cannot be empty"}), 400

    # Fetch known issues
    issues = df["Issue_Description"].dropna().tolist()
    best_match = process.extractOne(user_query, issues) if issues else None

    # ✅ Step 1: Improve Out-of-Domain Detection
    is_technical = any(keyword in user_query for keyword in TECHNICAL_KEYWORDS)

    if not best_match or best_match[1] < 75:  # 🔥 Reduced threshold to 75
        if is_technical:
            # If the query contains technical keywords, create an incident instead of rejecting it
            servicenow_response = create_servicenow_incident(user_query)

            return jsonify({
                "query": user_query,
                "incident_agent": "Creation Agent",
                "response": servicenow_response["message"],
                "assigned_team": ["User", "Create Incident", "End"],
                "incident_number": servicenow_response["incident_number"],
                "reassigned_team": servicenow_response["assignment_group"],
                "tech_debt_suggestions": "No significant tech debt identified."
            })
        else:
            return jsonify({
                "query": user_query,
                "incident_agent": "None",
                "response": random.choice(OUT_OF_DOMAIN_RESPONSES),
                "assigned_team": ["User", "End"],
                "tech_debt_suggestions": "No significant tech debt identified."
            })

    # Step 2: Fetch Matched Resolutions
    matched_incidents = df[df["Issue_Description"] == best_match[0]]
    past_resolutions = matched_incidents["Resolution"].dropna().tolist()
    incident_context = "\n".join([f"- {issue}: {res}" for issue, res in zip(matched_incidents["Issue_Description"], past_resolutions)])

    # Step 3: Call LLM for Incident Analysis
    response = analyze_incident(user_query, incident_context)
    response_text = response.content if hasattr(response, 'content') else str(response)

    # Step 4: Extract Suggested Resolutions
    suggested_resolutions = []
    if "Most Relevant Resolutions:" in response_text:
        resolutions_part = response_text.split("Most Relevant Resolutions:")[1].strip()
        suggested_resolutions = [res.strip("- ").strip() for res in resolutions_part.split("\n") if res.startswith("-")]

    # Step 5: Validate Suggested Resolutions Against Past Cases
    valid_resolution_found = any(res in past_resolutions for res in suggested_resolutions)

    # Step 6: External Validation for Hallucinated Responses
    if not valid_resolution_found:
        verification_response = validate_resolution_externally("\n".join(suggested_resolutions))
        verification_text = verification_response.content if hasattr(verification_response, 'content') else str(verification_response)

        # Step 7: If External Validation Fails, Create an Incident
        if "Hallucinated Resolution Detected" in verification_text:
            servicenow_response = create_servicenow_incident(user_query)

            return jsonify({
                "query": user_query,
                "incident_agent": "Creation Agent",
                "response": servicenow_response["message"],
                "assigned_team": ["User", "Create Incident", "End"],
                "incident_number": servicenow_response["incident_number"],
                "reassigned_team": servicenow_response["assignment_group"],
                "tech_debt_suggestions": "No significant tech debt identified."
            })

    # Step 8: Assign Correct Agent and Tech Debt Analysis
    incident_agent = "Analysis Agent"
    for line in response_text.split("\n"):
        if line.startswith("Incident Agent:"):
            incident_agent = line.replace("Incident Agent:", "").strip()
            break

    tech_debt_suggestions = assess_technical_debt(past_resolutions) if past_resolutions else "No significant tech debt identified."
    assigned_team_list = ["Incident Analysis"]
    if tech_debt_suggestions != "No significant tech debt identified.":
        assigned_team_list.append("Tech Debt Analysis")

    teams = ", ".join(df["Assigned_Team"].unique()) if not df.empty else "General Support"

    return jsonify({
        "query": user_query,
        "incident_agent": incident_agent,
        "response": response_text,
        "assigned_team": assigned_team_list + ["End"],
        "reassigned_team": teams,
        "tech_debt_suggestions": tech_debt_suggestions
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
