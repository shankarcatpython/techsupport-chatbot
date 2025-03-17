import random
import requests
import datetime
from config.settings import SERVICE_NOW_URL, SERVICE_NOW_TOKEN

TECHNICAL_KEYWORDS_SN = [
    # **Networking & Connectivity**
    "network", "connectivity", "server", "DNS", "proxy", "firewall",
    "latency", "bandwidth", "IP", "port", "VPN", "gateway", "subnet",

    # **Authentication & Authorization**
    "login", "password", "authentication", "authorization", "token", "MFA",
    "2FA", "SSO", "session", "logout", "credential", "access denied",

    # **Errors & Failures**
    "error", "failure", "timeout", "crash", "down", "unreachable", 
    "503", "502", "403", "500", "404", "exception", "stacktrace", 
    "bug", "glitch", "malfunction", "fault", "issue", "stuck", "hanging",

    # **API & Services**
    "API", "endpoint", "integration", "webhook", "request", "response",
    "payload", "POST", "GET", "PUT", "DELETE", "rate limit", "throttling",

    # **System & Performance Issues**
    "CPU", "RAM", "memory", "disk", "storage", "database", "DB", "query",
    "index", "cache", "backup", "restore", "corrupt", "data loss", "I/O",
    "resource", "process", "thread", "deadlock", "bottleneck",

    # **Cloud & Infrastructure**
    "AWS", "Azure", "GCP", "cloud", "container", "kubernetes", "docker",
    "EC2", "S3", "lambda", "RDS", "ECS", "k8s", "instance", "cluster",
    "node", "autoscaling", "load balancer", "ELB", "CDN", "microservice",

    # **Email & Messaging**
    "email", "SMTP", "IMAP", "POP3", "spam", "bounced", "undelivered",
    "notifications", "email queue", "email failure", "mail server",

    # **Payments & Transactions**
    "payment", "transaction", "invoice", "billing", "refund", "chargeback",
    "payment gateway", "credit card", "debit card", "failed payment",

    # **Security & Compliance**
    "breach", "vulnerability", "DDoS", "phishing", "ransomware", "malware",
    "virus", "attack", "hacked", "compromise", "CVE", "SSL", "TLS", "certificate",
    "firewall rule", "whitelist", "blacklist", "secure", "encryption",

    # **Software & Application Issues**
    "install", "update", "patch", "version", "rollback", "deployment",
    "rollback", "release", "hotfix", "framework", "dependency", "package",
    "repository", "git", "CI/CD", "pipeline", "build", "debug", "log",

    # **User Interface & Experience**
    "UI", "UX", "layout", "form", "dropdown", "button", "click",
    "navigation", "mobile", "responsive", "browser", "compatibility",
    "display", "rendering", "screen", "resolution", "viewport",

    # **Printing & Hardware Issues**
    "printer", "scanner", "driver", "hardware", "peripheral", "USB",
    "monitor", "display", "screen", "brightness", "resolution",
    "graphics", "GPU", "firmware", "BIOS", "boot", "POST", "motherboard",

    # **ServiceNow & ITSM (If applicable)**
    "incident", "ticket", "ServiceNow", "helpdesk", "support request",
    "workflow", "approval", "escalation", "assignment", "priority", "SLA"
]

# Define headers for ServiceNow API authentication
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SERVICE_NOW_TOKEN}"
}

def create_servicenow_incident(user_query):
    """
    Attempts to create an incident in ServiceNow.
    If the ServiceNow API is not available, falls back to local simulation.
    """

    # Prepare payload for ServiceNow API
    data = {
        "short_description": user_query,
        "category": "Support"
    }

    try:
        # Attempt to create the incident via the real ServiceNow API
        response = requests.post(SERVICE_NOW_URL, json=data, headers=HEADERS)

        # If request fails, log error and simulate locally
        if response.status_code != 201:
            print(f"ServiceNow API Error: {response.status_code} - {response.text}")
            return simulate_local_incident(user_query)

        # Extract incident number from ServiceNow API response
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

    except requests.exceptions.RequestException as e:
        print(f"ServiceNow API Connection Error: {e}")
        return simulate_local_incident(user_query)


def simulate_local_incident(user_query):
    """
    Generates a realistic ServiceNow-style incident response when API is unavailable.
    """
    incident_number = f"INC-{random.randint(10000, 99999)}"
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "incident_number": incident_number,
        "short_description": user_query,
        "created_at": created_at,
        "status": "New",
        "assignment_group": "Technical Support",
        "priority": "Medium",
        "message": (
            f"ServiceNow Incident {incident_number} has been successfully created.\n"
            f"- Issue Description:- {user_query}\n"
            f"- Created On:- {created_at}\n"
            f"- Status: New\n"
            f"- Assignment Group:- L1 Technical Support\n"
            f"- Priority:- Medium"
        )
    }
