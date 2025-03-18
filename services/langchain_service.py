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


def validate_technical_nature(query):
    """
    Uses LLM to determine if a query is technical or non-technical.
    Expands classification to better detect IT process-related issues.
    """
    messages = [
        {"role": "system", "content": "Classify whether this query is purely technical or non-technical. "
                                      "Consider both software/system issues and IT process-related problems. "
                                      "Respond ONLY with 'Technical' or 'Non-Technical'."},
        {"role": "user", "content": f"Query: {query}"}
    ]
    response = llm.invoke(messages)

    return response.content.strip() == "Technical" if hasattr(response, 'content') else False


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

    response_text = response.content if hasattr(response, 'content') else str(response)
    
    return response_text
