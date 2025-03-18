from flask import Flask, request, render_template, jsonify
import pandas as pd
import random
from api.endpoints import api_blueprint
from services.langchain_service import analyze_incident, assess_technical_debt, validate_technical_nature
from services.servicenow_api import create_servicenow_incident
from fuzzywuzzy import process

app = Flask(__name__, template_folder="templates", static_folder="static")
app.register_blueprint(api_blueprint)

df = pd.read_csv("data/incidents.csv")

OUT_OF_DOMAIN_RESPONSES = [
    "I'm here to assist with technical issues. Let me know if you need help with something tech-related.",
    "I specialize in resolving IT issues. Please provide a technical problem I can assist with."
]

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/ask', methods=['POST'])
def ask_llm():
    user_query = request.form.get("query", "").strip().lower()

    if not user_query:
        return jsonify({"error": "Query cannot be empty"}), 400

    # Validate if the query is actually technical
    is_technical = validate_technical_nature(user_query)

    # If the query is non-technical, return a direct response
    if not is_technical:
        return jsonify({
            "query": user_query,
            "incident_agent": None,
            "response": random.choice(OUT_OF_DOMAIN_RESPONSES),
            "assigned_team": ["User", "End"],
            "tech_debt_suggestions": None
        })

    # Fetch at least 5 best matches
    issues = df["Issue_Description"].dropna().tolist()
    best_matches = process.extract(user_query, issues, limit=5) if issues else []

    # If no strong match is found, create an incident
    if not best_matches or max(match[1] for match in best_matches) < 75:
        servicenow_response = create_servicenow_incident(user_query)

        return jsonify({
            "query": user_query,
            "incident_agent": "Creation Agent",
            "response": servicenow_response["message"],
            "incident_number": servicenow_response["incident_number"],
            "assigned_team": ["User", "Create Incident", "End"],
            "reassigned_team": servicenow_response["assignment_group"],
            "tech_debt_suggestions": None  # 🔥 No Tech Debt Suggestions if ticket created
        })

    # Retrieve resolutions from best matches
    matched_incidents = df[df["Issue_Description"].isin([match[0] for match in best_matches])]
    past_resolutions = matched_incidents["Resolution"].dropna().tolist()
    incident_context = "\n".join([f"- {issue}: {res}" for issue, res in zip(matched_incidents["Issue_Description"], past_resolutions)])

    # Analyze incident using LLM
    response = analyze_incident(user_query, incident_context)
    response_text = response.content if hasattr(response, 'content') else str(response)

    # Extract relevant resolutions
    suggested_resolutions = []
    if "Most Relevant Resolutions:" in response_text:
        resolutions_part = response_text.split("Most Relevant Resolutions:")[1].strip()
        suggested_resolutions = [res.strip("- ").strip() for res in resolutions_part.split("\n") if res.startswith("-")]

    # Extract dynamic incident agent type
    incident_agent = next((line.replace("Incident Agent:", "").strip()
                           for line in response_text.split("\n") if line.startswith("Incident Agent:")), "Analysis Agent")

    # Assess technical debt separately
    tech_debt_suggestions = assess_technical_debt(past_resolutions) if past_resolutions else None

    # Ensure "Tech Debt Suggestions:" phrase is removed, but "Agent: Tech Debt Agent" remains
    if tech_debt_suggestions and tech_debt_suggestions.startswith("Tech Debt Suggestions:"):
        tech_debt_suggestions = tech_debt_suggestions.replace("Tech Debt Suggestions:", "").strip()

    # Organize assigned teams dynamically
    assigned_team_list = []
    if "Analysis" in incident_agent:
        assigned_team_list.append("Incident Analysis")
    if tech_debt_suggestions:
        assigned_team_list.append("Tech Debt Analysis")

    return jsonify({
        "query": user_query,
        "incident_agent": incident_agent,
        "response": response_text,
        "assigned_team": assigned_team_list + ["End"],
        "reassigned_team": ", ".join(df["Assigned_Team"].unique()) if not df.empty else "General Support",
        "tech_debt_suggestions": tech_debt_suggestions
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
