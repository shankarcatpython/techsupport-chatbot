from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from services.langchain_service import analyze_incident, assess_technical_debt, validate_technical_nature
from services.servicenow_api import create_servicenow_incident
import pandas as pd
from fuzzywuzzy import process

# Load incident data
df = pd.read_csv("data/incidents.csv")

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o")

# Define properly formatted tool functions
def analyze_incident_tool(query: str) -> str:
    """Retrieves historical incident context and analyzes it."""
    issues = df["Issue_Description"].dropna().tolist()
    best_matches = process.extract(query, issues, limit=5) if issues else []
    
    if not best_matches:
        return "No relevant incidents found."

    matched_incidents = df[df["Issue_Description"].isin([match[0] for match in best_matches])]
    past_resolutions = matched_incidents["Resolution"].dropna().tolist()
    incident_context = "\n".join([f"- {issue}: {res}" for issue, res in zip(matched_incidents["Issue_Description"], past_resolutions)])

    return analyze_incident(query, incident_context).content

def validate_technical_nature_tool(query: str) -> str:
    """Validates if a query is technical or not."""
    return "Technical" if validate_technical_nature(query) else "Non-Technical"

def assess_technical_debt_tool(query: str) -> str:
    """Analyzes technical debt based on past resolutions."""
    return assess_technical_debt([query])

def create_incident_tool(query: str) -> dict:
    """Creates a new ServiceNow incident."""
    return create_servicenow_incident(query)

# Register tools correctly with single-argument functions
analyze_tool = Tool(
    name="analyze_incident",
    func=analyze_incident_tool,
    description="Analyzes an incident based on historical cases and suggests the best resolution."
)

validate_tool = Tool(
    name="validate_technical_nature",
    func=validate_technical_nature_tool,
    description="Classifies whether a user query is technical or non-technical."
)

tech_debt_tool = Tool(
    name="assess_technical_debt",
    func=assess_technical_debt_tool,
    description="Analyzes past resolutions to identify technical debt and suggest proactive measures."
)

create_tool = Tool(
    name="create_incident",
    func=create_incident_tool,
    description="Creates a ServiceNow incident when an issue lacks prior resolutions."
)

# Initialize memory for conversation tracking
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create LangChain Agent
agent_executor = initialize_agent(
    tools=[analyze_tool, validate_tool, tech_debt_tool, create_tool],
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    memory=memory,
    verbose=True
)

def handle_query(user_query: str) -> str:
    """Handles a user query through LangChain Agent."""
    result = agent_executor.run(user_query)
    return result
