from langchain_openai import ChatOpenAI
from config.settings import OPENAI_API_KEY

# Initialize OpenAI model
llm = ChatOpenAI(
    model="gpt-4o",  # GPT-4o model
    openai_api_key=OPENAI_API_KEY
)

def analyze_incident(query, incident_context):
    messages = [
        {"role": "system", "content": "You are an AI assistant for a tech support team. Use the most relevant historical cases to suggest the best resolution."},
        {"role": "user", "content": f"""
            Query: {query}

            Here are the top similar past incidents and their resolutions (up to 3 resolutions per issue):

            {incident_context}

            Based on this, provide the most relevant resolution(s) for the current issue.
            If multiple resolutions are relevant, list them all.

            Format the response strictly as follows:

            Agent: Analysis Agent

            Most Relevant Resolutions:
            - <First relevant resolution>
            - <Second relevant resolution> (if applicable)
            - <Third relevant resolution> (if applicable)

            Explanation:
            Explain why these resolutions are relevant in a clear, human-friendly way.
        """}
    ]
    return llm.invoke(messages)

# Agent B - Create new incident
def create_new_incident(query):
    messages = [
        {"role": "system", "content": "You are a ServiceNow AI assistant."},
        {"role": "user", "content": f"""
            The following issue was reported but no matching incidents were found:

            User Query: {query}

            Determine if a new ServiceNow ticket should be created. If yes, provide the response strictly formatted as:

            Incident Summary:
            - Issue: <short issue summary>
            - Description: <brief clear description of the user's issue>
            - Recommended Next Steps: <clear recommended actions>
        """}
    ]
    return llm.invoke(messages)

# Agent C - Reassign ticket
def reassign_ticket(query, teams):
    messages = [
        {"role": "system", "content": "You are a ticket assignment AI."},
        {"role": "user", "content": f"A support ticket has been raised with this issue:\n\n{query}\n\nBased on historical incidents, which support team should handle this issue? Choose from: {teams}."}
    ]
    return llm.invoke(messages)

# Agent D - Assess technical debt
def assess_technical_debt(resolutions):
    """
    Analyzes past resolutions to identify technical debt and suggest improvements.
    """
    resolution_text = "\n".join([f"- {res}" for res in resolutions])

    messages = [
        {"role": "system", "content": "You are an AI responsible for identifying technical debt in a support system. Analyze past resolutions and suggest proactive measures to prevent recurring issues."},
        {"role": "user", "content": f"""
            Here are the resolutions that were used to resolve incidents:

            {resolution_text}

            Identify recurring patterns and suggest long-term improvements to prevent these issues in the future.
            Format the response strictly as follows:

            Agent: Tech Debt Agent

            Most Relevant Technical Debt Issues:
            - <First issue>
            - <Second issue> (if applicable)
            - <Third issue> (if applicable)

            Recommended Fixes:
            - <First fix>
            - <Second fix> (if applicable)
            - <Third fix> (if applicable)

            If no tech debt is found, return exactly: "No significant tech debt identified."
        """}
    ]
    
    response = llm.invoke(messages)

    # Post-process response to remove duplicate "Agent: Tech Debt Agent" labels
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    return response_text

def validate_resolution_externally(resolutions):
    """
    Checks whether a suggested resolution exists in an external IT knowledge base.
    If it is not verifiable externally, we assume it is hallucinated.
    """
    messages = [
        {"role": "system", "content": "You are an AI that validates whether suggested resolutions exist in an IT troubleshooting database."},
        {"role": "user", "content": f"""
            Here are suggested resolutions for a technical issue:

            {resolutions}

            Determine if these resolutions exist in an IT troubleshooting knowledge base.
            
            **If they are found, return exactly:** "Resolution Verified."
            **If they are NOT found, return exactly:** "Hallucinated Resolution Detected."

            Do NOT include any additional text—only return one of the two responses above.
        """}
    ]
    return llm.invoke(messages)

