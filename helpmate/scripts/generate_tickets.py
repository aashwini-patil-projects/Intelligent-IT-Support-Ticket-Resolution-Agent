import pandas as pd
import random
from datetime import datetime, timedelta
from faker import Faker
import json

fake = Faker()
random.seed(42)
Faker.seed(42)

# Configuration
CATEGORIES = ["Hardware", "Software", "Network", "Account/Access", "Email", "VPN", "Printing", "Security"]
DEPARTMENTS = ["Sales", "Finance", "Engineering", "HR", "Ops"]
CHANNELS = ["Email", "Portal", "Phone", "Chat"]
PRIORITIES = ["P1", "P2", "P3", "P4"]
STATUSES = ["Resolved", "Closed"]
RESOLUTION_CODES = ["Fixed", "Workaround", "Duplicate", "No Issue Found", "User Education", "Escalated"]
SYSTEMS = {
    "Hardware": ["Laptop", "Desktop", "Monitor", "Docking Station", "Keyboard"],
    "Software": ["Outlook", "Teams", "Chrome", "CRM", "ERP"],
    "Network": ["VPN", "WiFi", "Ethernet", "Firewall"],
    "Account/Access": ["Active Directory", "Azure AD", "SSO", "Badge Access"],
    "Email": ["Outlook", "Exchange Server", "Mail Gateway"],
    "VPN": ["VPN", "Cisco AnyConnect", "Pulse Secure"],
    "Printing": ["Printer", "Print Server", "Scanner"],
    "Security": ["Antivirus", "Firewall", "MFA", "Security Token"]
}

# Issue templates for realistic tickets
ISSUE_TEMPLATES = {
    "VPN": [
        ("Cannot connect to VPN from home", "VPN client shows error 'Connection timeout' when trying to connect from home network. Started happening after yesterday's update."),
        ("VPN disconnects every few minutes", "VPN connection drops randomly every 5-10 minutes. Have to reconnect multiple times during work."),
        ("VPN authentication failed", "Getting 'Authentication failed' error when entering correct credentials. Tried resetting password but still fails."),
        ("Slow VPN connection", "VPN connects but internet speed is extremely slow. Downloads timing out, Teams calls dropping."),
    ],
    "Email": [
        ("Cannot send emails - stuck in outbox", "Emails are getting stuck in outbox and not sending. Receiving emails works fine."),
        ("Outlook keeps crashing", "Outlook crashes every time I try to open it. Getting error message about .pst file."),
        ("Not receiving external emails", "Internal emails work fine but not receiving any emails from external domains since this morning."),
        ("Mailbox full - cannot receive emails", "Getting bounce-back messages saying my mailbox is full. Need quota increased."),
    ],
    "Account/Access": [
        ("Account locked out", "My account got locked after entering wrong password. Cannot login to any system now."),
        ("Cannot access shared folder", "Getting 'Access Denied' when trying to open \\\\fileserver\\shared. I had access yesterday."),
        ("Password reset not working", "Tried using self-service password reset portal but not receiving the verification code."),
        ("New employee needs access", "New team member started today and needs access to CRM, email, and file shares."),
    ],
    "Hardware": [
        ("Laptop won't turn on", "Laptop not powering on. Tried different power outlets and checked charger LED is on."),
        ("Blue screen on startup", "Getting blue screen error on Windows startup. Error code: DRIVER_IRQL_NOT_LESS_OR_EQUAL."),
        ("Laptop overheating and shutting down", "Laptop getting very hot and shutting down randomly during work. Fan making loud noise."),
        ("Monitor not displaying", "External monitor shows 'No Signal' when connected to laptop. Built-in screen works fine."),
    ],
    "Software": [
        ("Teams not loading chats", "Microsoft Teams opens but chat messages not loading. Shows 'Connecting' forever."),
        ("CRM application login error", "CRM shows 'Server unavailable' error when trying to login. Colleagues can access fine."),
        ("Excel file corrupted", "Cannot open important Excel file. Getting error 'File is corrupted and cannot be opened'."),
        ("Software installation request", "Need Adobe Acrobat Pro installed for contract reviews. Current version is Reader only."),
    ],
    "Network": [
        ("No internet connection", "Computer connected to network but no internet access. Yellow triangle icon on network."),
        ("Cannot access internal websites", "External websites load fine but internal intranet and applications not accessible."),
        ("Slow network speed", "Network extremely slow today. File transfers timing out, web pages taking forever to load."),
        ("WiFi keeps disconnecting", "WiFi connection drops every few minutes. Ethernet cable works but need WiFi for mobility."),
    ],
    "Printing": [
        ("Printer not responding", "Print jobs sent to printer but nothing prints. Printer shows ready status."),
        ("Print queue stuck", "Documents stuck in print queue. Cannot print or delete them. Tried restarting computer."),
        ("Print quality issues", "Printouts have faded text and streaks. Tried printing test page with same result."),
        ("Cannot find network printer", "Network printer disappeared from my printer list. Used to work last week."),
    ],
    "Security": [
        ("MFA token not working", "MFA authentication token showing 'Invalid code' even though entering correct numbers."),
        ("Antivirus blocking application", "Antivirus keeps quarantining work application. Cannot complete tasks without it."),
        ("Suspicious email received", "Received phishing email claiming to be from IT asking for password. Reporting for investigation."),
        ("Security certificate error", "Getting security certificate warning when accessing company portal. Certificate expired?"),
    ]
}

def generate_tickets(num_tickets=150):
    tickets = []
    case_counter = 1
    
    # Weight categories - VPN and Email are more common
    category_weights = [10, 15, 12, 18, 20, 25, 8, 7]
    
    for i in range(1, num_tickets + 1):
        ticket_id = f"TCK-{i:05d}"
        category = random.choices(CATEGORIES, weights=category_weights)[0]
        
        # Select subject and description from templates
        if category in ISSUE_TEMPLATES:
            subject, description = random.choice(ISSUE_TEMPLATES[category])
        else:
            subject = f"Issue with {category}"
            description = f"User reported problem with {category} system."
        
        # Priority distribution: mostly P3/P4 (80%), some P2 (15%), rare P1 (5%)
        priority = random.choices(PRIORITIES, weights=[5, 15, 40, 40])[0]
        
        # System affected
        affected_system = random.choice(SYSTEMS.get(category, ["General"]))
        
        # Status - all resolved or closed for training data
        status = random.choice(STATUSES)
        
        # Resolution code based on probability
        resolution_code = random.choices(
            RESOLUTION_CODES,
            weights=[50, 20, 10, 8, 10, 2]
        )[0]
        
        # Case ID - only escalated tickets get case IDs (about 5%)
        case_id = None
        if resolution_code == "Escalated" or (priority == "P1" and random.random() < 0.3):
            case_id = f"CASE-{case_counter:05d}"
            case_counter += 1
            resolution_code = "Escalated"
        
        # Time to resolve based on priority
        if priority == "P1":
            time_to_resolve = random.uniform(0.5, 4)
        elif priority == "P2":
            time_to_resolve = random.uniform(2, 12)
        elif priority == "P3":
            time_to_resolve = random.uniform(4, 48)
        else:
            time_to_resolve = random.uniform(8, 120)
        
        # SLA breach more likely for P1/P2
        sla_breached = "No"
        if priority == "P1" and time_to_resolve > 4:
            sla_breached = "Yes"
        elif priority == "P2" and time_to_resolve > 24:
            sla_breached = "Yes"
        
        # Reopened more likely for workarounds and no issue found
        reopened_prob = 0.05
        if resolution_code in ["Workaround", "No Issue Found"]:
            reopened_prob = 0.25
        reopened = "Yes" if random.random() < reopened_prob else "No"
        
        # CSAT - lower if reopened or SLA breached
        if reopened == "Yes" or sla_breached == "Yes":
            csat = random.choices([1, 2, 3, 4, 5], weights=[15, 25, 35, 20, 5])[0]
        else:
            csat = random.choices([1, 2, 3, 4, 5], weights=[2, 5, 15, 40, 38])[0]
        
        # Created date - spread over last 6 months
        created_at = datetime.now() - timedelta(days=random.randint(1, 180), 
                                                 hours=random.randint(0, 23),
                                                 minutes=random.randint(0, 59))
        
        ticket = {
            "ticket_id": ticket_id,
            "case_id": case_id,
            "created_at": created_at.strftime("%Y-%m-%dT%H:%M"),
            "requester_id": f"USR-{random.randint(100, 999):05d}",
            "department": random.choice(DEPARTMENTS),
            "channel": random.choice(CHANNELS),
            "category": category,
            "affected_system": affected_system,
            "priority": priority,
            "subject": subject,
            "description": description,
            "status": status,
            "assignee_id": f"TECH-{random.randint(1, 8):02d}",
            "resolution_code": resolution_code,
            "time_to_resolve_hours": round(time_to_resolve, 2),
            "reopened": reopened,
            "sla_breached": sla_breached,
            "csat": csat
        }
        
        tickets.append(ticket)
    
    return pd.DataFrame(tickets)

if __name__ == "__main__":
    # Generate tickets
    df = generate_tickets(150)
    
    # Save to CSV
    df.to_csv("data/tickets.csv", index=False)
    print(f"Generated {len(df)} tickets")
    print(f"\nCategory distribution:\n{df['category'].value_counts()}")
    print(f"\nPriority distribution:\n{df['priority'].value_counts()}")
    print(f"\nResolution code distribution:\n{df['resolution_code'].value_counts()}")
    print(f"\nEscalated cases: {df['case_id'].notna().sum()}")
