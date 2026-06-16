import pandas as pd
import random
import json
from datetime import datetime

random.seed(42)

# Resolution note templates following the required structure
RESOLUTION_TEMPLATES = {
    "VPN": {
        "connection_timeout": {
            "summary": "User experienced VPN connection timeout errors preventing remote access to corporate network. Issue began following recent VPN client update.",
            "diagnosis": "Root cause identified as incompatible VPN client version conflicting with new firewall rules deployed in recent security update.",
            "resolution": "1. Uninstalled current VPN client version\n2. Downloaded and installed VPN client v5.2.1 from IT portal\n3. Cleared cached credentials\n4. Reconnected using fresh authentication\n5. Verified stable connection for 30 minutes",
            "verification": "User successfully connected to VPN and accessed file shares and internal applications without disconnection for extended testing period.",
            "preventive": "Updated KB article with compatibility matrix. Scheduled automated deployment of correct VPN client version to all endpoints.",
        },
        "frequent_disconnect": {
            "summary": "VPN connection randomly disconnecting every 5-10 minutes requiring manual reconnection. Multiple users in Engineering department affected.",
            "diagnosis": "Network timeout settings too aggressive after infrastructure upgrade. Default keepalive interval increased from 30s to 60s causing idle disconnections.",
            "resolution": "1. Accessed VPN concentrator admin panel\n2. Modified keepalive interval from 60s back to 30s\n3. Adjusted idle timeout from 5 minutes to 15 minutes\n4. Restarted VPN service\n5. Monitored connection stability",
            "verification": "Monitored 20 affected users over 4 hours. No disconnections reported. VPN logs show stable sessions.",
            "preventive": "Documented optimal timeout settings in runbook. Added monitoring alert for spike in VPN reconnection events.",
        },
        "auth_failed": {
            "summary": "User unable to authenticate to VPN despite correct password. Account not locked in Active Directory.",
            "diagnosis": "User's VPN authentication profile corrupted. MFA token out of sync with authentication server by 45 seconds.",
            "resolution": "1. Reset VPN profile on authentication server\n2. Synchronized MFA token with NTP time server\n3. Cleared user's cached VPN credentials\n4. Re-enrolled MFA token\n5. Test authentication successful",
            "verification": "User successfully authenticated using password and MFA token. Tested from two different networks.",
            "preventive": "Created KB article for MFA time sync issue. Implemented automated time sync check in VPN client.",
        }
    },
    "Email": {
        "stuck_outbox": {
            "summary": "User unable to send emails with messages stuck in Outlook outbox. Receiving emails functioning normally.",
            "diagnosis": "Oversized email attachment (35MB) exceeding mail server limit of 25MB causing send queue blockage. PST file not corrupted.",
            "resolution": "1. Opened Outlook in safe mode\n2. Located stuck email with large attachment in outbox\n3. Deleted problematic email\n4. Resent email using file sharing link instead of attachment\n5. Verified send queue cleared",
            "verification": "User sent test emails with normal attachments successfully. Outbox cleared and email flow restored.",
            "preventive": "Updated email policy KB article with attachment size limits. Configured warning prompt for attachments over 20MB.",
        },
        "outlook_crash": {
            "summary": "Outlook application crashes immediately on startup with error referencing PST file corruption.",
            "diagnosis": "PST file corruption detected. File size exceeded 50GB limit for older PST format. Corruption in file structure causing application crash.",
            "resolution": "1. Closed Outlook and all Office applications\n2. Ran inbox repair tool (scanpst.exe) on PST file\n3. Repair tool fixed 247 errors in file structure\n4. Created new PST file and migrated recent emails\n5. Archived old PST as backup",
            "verification": "Outlook launched successfully. User accessed all emails and folders. No crashes during 2-hour monitoring period.",
            "preventive": "Enabled online archive to prevent PST file growth. Scheduled monthly PST maintenance for affected users.",
        },
        "external_email_block": {
            "summary": "User and 15 colleagues in Sales department not receiving external emails since 8 AM. Internal emails working correctly.",
            "diagnosis": "Sales distribution group accidentally added to email gateway block list during spam filter update. Configuration error in mail flow rule.",
            "resolution": "1. Checked mail gateway logs for blocked messages\n2. Identified Sales group in block list\n3. Removed Sales group from block list\n4. Released 127 quarantined emails\n5. Verified mail flow restored",
            "verification": "Sent test external emails to affected users. All received within 2 minutes. Monitored for 1 hour - no issues.",
            "preventive": "Added approval workflow for mail flow rule changes. Updated change management process documentation.",
        }
    },
    "Account/Access": {
        "account_lockout": {
            "summary": "User account locked after multiple failed login attempts. User unable to access any corporate systems.",
            "diagnosis": "Account locked due to password policy after 5 failed attempts. Old saved credentials in mobile device continuing to attempt login causing repeated locks.",
            "resolution": "1. Unlocked user account in Active Directory\n2. Reset password using secure channel\n3. Identified mobile device with cached old credentials\n4. Updated credentials on mobile device\n5. Verified no further lockout attempts",
            "verification": "User successfully logged into workstation, VPN, and email. Monitored account for 24 hours with no lockout events.",
            "preventive": "Educated user on credential caching. Created KB article on common lockout causes and mobile device credential management.",
        },
        "shared_folder_access": {
            "summary": "User suddenly unable to access shared folder on file server with 'Access Denied' error. Previous access confirmed.",
            "diagnosis": "User account accidentally removed from security group during recent group membership cleanup. Permission inherited from group, not direct assignment.",
            "resolution": "1. Checked file server permissions\n2. Verified user not in required security group 'FileShare_Sales_RW'\n3. Re-added user to security group\n4. Forced group policy update (gpupdate /force)\n5. User logged off and back on to refresh token",
            "verification": "User successfully accessed shared folder. Tested read and write permissions. All file operations working.",
            "preventive": "Implemented review process before group membership changes. Added monitoring for removed users from critical groups.",
        }
    },
    "Hardware": {
        "laptop_no_power": {
            "summary": "User laptop not powering on despite charger LED indicator showing power supply active.",
            "diagnosis": "Complete power drain combined with BIOS battery failure preventing startup. Motherboard requiring hard reset to recover from power state.",
            "resolution": "1. Disconnected charger and removed battery\n2. Held power button for 60 seconds to discharge residual power\n3. Reconnected charger (without battery)\n4. Laptop successfully powered on\n5. Replaced BIOS battery, reinserted main battery",
            "verification": "Laptop booted successfully. Ran hardware diagnostics - all tests passed. Verified battery charging correctly.",
            "preventive": "Updated laptop troubleshooting KB article. Scheduled BIOS battery replacement for laptops over 3 years old.",
        },
        "blue_screen": {
            "summary": "User experiencing blue screen errors on Windows startup with driver-related error code. Laptop unusable.",
            "diagnosis": "Outdated network adapter driver incompatible with recent Windows update. Driver version 2.3.1 causing IRQL error, latest compatible version is 3.1.5.",
            "resolution": "1. Booted laptop in Safe Mode\n2. Opened Device Manager and located network adapter\n3. Uninstalled network adapter driver\n4. Downloaded driver version 3.1.5 from manufacturer site\n5. Installed updated driver and restarted",
            "verification": "Laptop booted normally without blue screen. Tested network connectivity. Ran stress test for 2 hours - no crashes.",
            "preventive": "Added network driver to approved software list. Scheduled automatic driver updates via SCCM.",
        }
    },
    "Software": {
        "teams_not_loading": {
            "summary": "Microsoft Teams application opening but chat messages not loading. Status stuck on 'Connecting...'.",
            "diagnosis": "Teams cache corruption after interrupted update. Local data files corrupted preventing synchronization with Teams service.",
            "resolution": "1. Closed Teams completely (including system tray)\n2. Cleared Teams cache from %appdata%\\Microsoft\\Teams\n3. Cleared Teams cache from %localappdata%\\Microsoft\\Teams\n4. Restarted Teams application\n5. Application rebuilt cache and synchronized",
            "verification": "Teams loaded all chats and messages. Tested sending/receiving messages. Voice call test successful.",
            "preventive": "Created KB article for Teams cache issues. Added Teams cache clear script to self-service portal.",
        }
    },
    "Network": {
        "no_internet": {
            "summary": "User computer connected to corporate network but unable to access internet. Yellow warning icon on network indicator.",
            "diagnosis": "DNS server configuration incorrect. Computer receiving old DNS server IP addresses from DHCP due to stale reservation. DNS servers decommissioned last month.",
            "resolution": "1. Released current IP configuration (ipconfig /release)\n2. Flushed DNS cache (ipconfig /flushdns)\n3. Renewed IP configuration (ipconfig /renew)\n4. Verified new DNS server addresses received\n5. Tested internet connectivity",
            "verification": "User accessed external websites successfully. Pinged multiple internet hosts. DNS resolution working correctly.",
            "preventive": "Removed stale DHCP reservations. Updated DHCP scope with current DNS servers.",
        }
    },
    "Printing": {
        "printer_not_responding": {
            "summary": "User print jobs sent to network printer but documents not printing. Printer status shows ready.",
            "diagnosis": "Print spooler service stopped on user's computer. Service crashed due to corrupted print job from third-party PDF application.",
            "resolution": "1. Restarted print spooler service\n2. Cleared print queue folder (C:\\Windows\\System32\\spool\\PRINTERS)\n3. Removed and re-added network printer\n4. Sent test print - successful\n5. Updated PDF application to latest version",
            "verification": "User successfully printed multiple documents. Tested different file types. Print queue functioning normally.",
            "preventive": "Added print spooler monitoring. Created automated restart script for spooler crashes.",
        }
    },
    "Security": {
        "mfa_invalid": {
            "summary": "User MFA token consistently showing 'Invalid code' error preventing system access. Token generates codes but all rejected.",
            "diagnosis": "MFA token time drift. Device clock 3 minutes ahead of authentication server causing TOTP codes to be out of valid time window.",
            "resolution": "1. Verified time sync issue on authentication server logs\n2. Synchronized mobile device time with network time\n3. Disabled and re-enabled automatic time zone\n4. Generated new MFA code after sync\n5. Authentication successful",
            "verification": "User successfully authenticated with MFA token. Tested multiple times over 30 minutes. All authentications successful.",
            "preventive": "Created KB article on MFA time sync requirements. Added time sync check to MFA enrollment process.",
        }
    }
}

# KB Articles
KB_ARTICLES = [
    {
        "kb_id": "KB-0001",
        "title": "VPN Connection Troubleshooting Guide",
        "category": "VPN",
        "content": """
**Overview**: This guide helps resolve common VPN connectivity issues.

**Prerequisites**: 
- VPN client v5.2.1 or later installed
- Valid corporate credentials
- MFA token enrolled

**Common Issues and Solutions**:

1. Connection Timeout
   - Check internet connectivity
   - Verify VPN server address: vpn.company.com
   - Disable other VPN clients
   - Temporarily disable antivirus for testing
   - Clear VPN client cache: Settings > Advanced > Clear Cache

2. Authentication Failures
   - Verify username format: domain\\username
   - Ensure password not expired (check email for expiry notices)
   - Check MFA token time sync with device clock
   - Contact IT if account locked (5 failed attempts)

3. Frequent Disconnections
   - Update VPN client to latest version
   - Check power saving settings (disable network adapter sleep)
   - Switch VPN protocol: Settings > Protocol > Try UDP or TCP
   - Disable IPv6 if experiencing routing issues

**Known Issues**:
- VPN client v5.1.x incompatible with Windows 11 - upgrade required
- Public WiFi networks may block VPN ports - try mobile hotspot

**Support**: For unresolved issues, contact IT Support with error codes and vpn_log.txt file.
""",
        "last_updated": "2024-12-15"
    },
    {
        "kb_id": "KB-0002",
        "title": "Email Attachment Size Limits and Best Practices",
        "category": "Email",
        "content": """
**Email Attachment Limits**:
- Maximum attachment size: 25MB per email
- Maximum total mailbox size: 50GB
- Shared mailbox limit: 100GB

**Best Practices for Large Files**:

1. Use SharePoint/OneDrive Links
   - Upload file to SharePoint or OneDrive
   - Share link via email instead of attachment
   - Set appropriate permissions (view/edit)
   - Benefits: No size limit, version control, collaboration

2. File Compression
   - Compress files using ZIP before attaching
   - Can reduce size by 50-70% for documents
   - Password protect sensitive compressed files

3. File Transfer Service
   - Use corporate file transfer portal for files over 100MB
   - Access at: https://filetransfer.company.com
   - Files retained for 14 days
   - Email notification sent to recipient with download link

**Common Issues**:
- Emails stuck in outbox: Usually caused by oversized attachments
- Solution: Delete stuck email, resend using file sharing link

**Warning Signs**:
- "Mailbox full" errors: Time to archive old emails
- Slow Outlook performance: Large PST file, enable online archive

**Support**: Contact IT to request mailbox quota increase if business justified.
""",
        "last_updated": "2024-12-10"
    },
    {
        "kb_id": "KB-0003",
        "title": "Account Lockout Prevention and Recovery",
        "category": "Account/Access",
        "content": """
**Account Lockout Policy**:
- Lockout threshold: 5 failed login attempts
- Lockout duration: 30 minutes (automatic unlock) or manual IT unlock
- Password expiry: 90 days

**Common Causes of Account Lockout**:

1. Cached Credentials on Devices
   - Mobile phone with old password
   - Tablet apps with saved credentials
   - Mapped network drives with stored credentials
   - Background sync applications

2. Password Expiry
   - Check email for password expiry notifications (sent 14 days before)
   - Use self-service portal to change password before expiry

3. Multiple Login Attempts
   - CapsLock enabled when entering password
   - Copy-pasting password with extra spaces
   - Using old password from password manager

**Self-Service Recovery**:
1. Wait 30 minutes for automatic unlock, OR
2. Use self-service portal: https://passwordreset.company.com
3. Verify identity using registered mobile number or security questions
4. Reset password following complexity requirements

**Password Requirements**:
- Minimum 12 characters
- At least one uppercase, lowercase, number, special character
- Cannot reuse last 10 passwords
- Cannot contain username or common words

**Prevention Tips**:
- Update credentials on ALL devices after password change
- Use company password manager for secure storage
- Enable password expiry notifications
- Check account status at: https://myaccount.company.com

**Support**: If locked and cannot self-recover, contact IT Service Desk with employee ID.
""",
        "last_updated": "2024-12-18"
    },
    {
        "kb_id": "KB-0004",
        "title": "Laptop Hardware Troubleshooting - Power Issues",
        "category": "Hardware",
        "content": """
**No Power / Won't Turn On**:

**Step 1: Basic Checks**
- Verify charger LED is lit (power reaching charger)
- Check power outlet with another device
- Inspect charger cable for damage
- Try different power outlet

**Step 2: Hard Reset**
1. Disconnect charger
2. Remove battery (if removable)
3. Hold power button for 60 seconds
4. Reconnect charger only (no battery)
5. Attempt to power on
6. If successful, reinsert battery

**Step 3: LED Indicator Diagnosis**
- No LED: Charger or power jack issue
- Orange blinking: Battery critical, charge for 30 minutes
- White steady: Normal, try power button

**Battery Issues**:

1. Not Charging
   - Check charging icon in system tray
   - Update battery driver in Device Manager
   - Run battery health diagnostic: Battery Health Tool
   - Replace battery if health < 50%

2. Rapid Drain
   - Check for resource-intensive processes (Task Manager)
   - Disable unnecessary startup programs
   - Lower screen brightness
   - Update BIOS to latest version

**Overheating**:
- Verify vents not blocked (use on hard surface)
- Clean air vents with compressed air
- Update thermal management drivers
- Check for Windows updates causing CPU spikes
- Consider laptop cooling pad for heavy workloads

**When to Escalate**:
- Hard reset doesn't work: Hardware failure likely
- Battery health < 30%: Replacement needed
- Physical damage to ports or case
- Liquid damage: Immediate escalation, do not power on

**Support**: For hardware failures, create ticket with laptop serial number for replacement/repair.
""",
        "last_updated": "2024-12-05"
    },
    {
        "kb_id": "KB-0005",
        "title": "Microsoft Teams Cache and Performance Issues",
        "category": "Software",
        "content": """
**Common Teams Issues**:
- Chats not loading
- Stuck on "Connecting..."
- Missing messages
- Video/audio call problems
- Slow performance

**Solution: Clear Teams Cache**

**Windows**:
1. Completely quit Teams:
   - Right-click Teams icon in system tray
   - Select "Quit"
   - Open Task Manager (Ctrl+Shift+Esc)
   - End any remaining Teams processes

2. Clear cache folders:
   - Press Windows+R
   - Navigate to: %appdata%\\Microsoft\\Teams
   - Delete all folders except "Backgrounds" and "Themes"
   - Navigate to: %localappdata%\\Microsoft\\Teams
   - Delete all contents

3. Restart Teams
   - Teams will rebuild cache on startup
   - Sign in with corporate credentials
   - Wait 2-3 minutes for full synchronization

**Mac**:
1. Quit Teams: Command+Q
2. Clear cache:
   - ~/Library/Application Support/Microsoft/Teams
   - Delete cache folders
3. Restart Teams

**Other Solutions**:

1. Update Teams
   - Teams auto-updates but can check manually
   - Click profile picture > Check for updates
   - Restart after update

2. Disable GPU Acceleration
   - Settings > General > Disable GPU hardware acceleration
   - Helps with graphics-related crashes

3. Reset Teams
   - Uninstall Teams
   - Delete cache folders
   - Reinstall from company portal

**Performance Tips**:
- Close unused chats and tabs
- Disable animations: Settings > General > Disable animations
- Limit number of teams/channels
- Use web version for lightweight access

**Support**: If issues persist after cache clear, report with Teams version number (Help > About).
""",
        "last_updated": "2024-12-12"
    },
    {
        "kb_id": "KB-0006",
        "title": "Network Printer Setup and Troubleshooting",
        "category": "Printing",
        "content": """
**Add Network Printer**:

**Windows**:
1. Open Settings > Devices > Printers & Scanners
2. Click "Add a printer or scanner"
3. Wait for scan, then click "The printer that I want isn't listed"
4. Select "Select a shared printer by name"
5. Enter: \\\\printserver\\[printer-name]
6. Click Next and follow prompts

**Common Printer Names**:
- \\\\printserver\\Floor1-Color-HP
- \\\\printserver\\Floor2-BW-Canon
- \\\\printserver\\Finance-Secure-Print

**Troubleshooting**:

1. Printer Not Found
   - Verify network connection
   - Check VPN connected if remote
   - Ping print server: ping printserver
   - Contact IT if print server unreachable

2. Jobs Not Printing
   - Check printer status: Settings > Printers
   - Look for "Offline" or "Paused" status
   - Right-click printer > "Use Printer Online"
   - Cancel stuck jobs and resubmit

3. Print Spooler Issues
   - Open Services (services.msc)
   - Find "Print Spooler"
   - Restart service
   - If fails, run as admin: net stop spooler && net start spooler

4. Driver Issues
   - Remove printer completely
   - Delete driver: Print Server Properties > Drivers
   - Reinstall printer (drivers auto-install from server)

**Print Quality Issues**:
- Faded output: Low toner (check printer display)
- Streaks: Clean print heads via printer menu
- Smudges: Check paper type matches setting

**Secure Print Release**:
1. Send print job from computer
2. Walk to printer
3. Tap badge on card reader
4. Select your print job
5. Press Print

**Support**: For hardware issues (paper jams, errors), report printer name and location to Facilities.
""",
        "last_updated": "2024-11-28"
    },
    {
        "kb_id": "KB-0007",
        "title": "Multi-Factor Authentication (MFA) Setup and Troubleshooting",
        "category": "Security",
        "content": """
**MFA Enrollment**:

1. Initial Setup
   - Visit: https://mfa.company.com
   - Sign in with corporate credentials
   - Choose MFA method: Mobile app (recommended) or SMS

2. Mobile App Setup (Microsoft Authenticator)
   - Install Microsoft Authenticator from app store
   - Click "Add account" > "Work or school account"
   - Scan QR code displayed on enrollment page
   - Complete test verification

3. Backup Methods
   - Always register 2+ methods
   - Add phone number for SMS backup
   - Print recovery codes and store securely

**Troubleshooting**:

1. "Invalid Code" Error
   - Cause: Time sync issue between device and server
   - Solution:
     * Enable automatic time/date on device
     * Disable then re-enable automatic time zone
     * Wait 2-3 minutes for sync
     * Generate fresh code

2. Not Receiving SMS
   - Verify phone number correct in profile
   - Check cellular signal strength
   - Try alternative backup method
   - Contact IT to verify number on file

3. Lost Device / New Phone
   - Use backup method to authenticate
   - Visit MFA portal to remove old device
   - Enroll new device following setup steps
   - If no backup access: Contact IT with employee ID for manual reset

4. App Not Generating Codes
   - Force close and reopen Authenticator app
   - Check app not in battery optimization (Android)
   - Reinstall Authenticator app
   - Re-enroll account

**Best Practices**:
- Never share MFA codes
- Approve only push notifications you initiated
- Report suspicious MFA prompts to Security team
- Keep backup methods current
- Re-enroll MFA when changing phones

**Security Tip**: If receiving unexpected MFA push notifications, DO NOT approve. This indicates someone attempting to access your account with your password. Immediately change password and report to IT Security.

**Support**: For MFA lockout (lost device + no backup), contact IT Service Desk with government-issued ID for identity verification.
""",
        "last_updated": "2024-12-20"
    }
]

def generate_resolved_tickets_corpus(tickets_df, num_resolutions=25):
    """Generate resolution notes for a subset of tickets"""
    corpus = []
    
    # Select diverse tickets for resolution notes
    resolved_tickets = tickets_df[
        (tickets_df['resolution_code'].isin(['Fixed', 'Workaround'])) &
        (tickets_df['category'].isin(RESOLUTION_TEMPLATES.keys()))
    ].sample(n=min(num_resolutions, len(tickets_df)), random_state=42)
    
    for _, ticket in resolved_tickets.iterrows():
        category = ticket['category']
        
        # Select appropriate template
        template_keys = list(RESOLUTION_TEMPLATES[category].keys())
        if not template_keys:
            continue
            
        template_key = random.choice(template_keys)
        template = RESOLUTION_TEMPLATES[category][template_key]
        
        # Create resolution note
        resolution_note = {
            "ticket_id": ticket['ticket_id'],
            "case_id": ticket['case_id'],
            "category": category,
            "affected_system": ticket['affected_system'],
            "priority": ticket['priority'],
            "subject": ticket['subject'],
            "summary": template['summary'],
            "affected_scope": f"User: {ticket['requester_id']}, Department: {ticket['department']}, System: {ticket['affected_system']}",
            "diagnosis": template['diagnosis'],
            "resolution": template['resolution'],
            "verification": template['verification'],
            "preventive_action": template['preventive'],
            "references": f"Ticket {ticket['ticket_id']}, Assigned to {ticket['assignee_id']}, Resolved in {ticket['time_to_resolve_hours']} hours",
            "resolved_by": ticket['assignee_id'],
            "resolved_at": ticket['created_at']
        }
        
        corpus.append(resolution_note)
    
    return corpus

def save_knowledge_corpus():
    """Generate and save the complete knowledge corpus"""
    # Load tickets
    tickets_df = pd.read_csv("data/tickets.csv")
    
    # Generate resolution notes
    resolution_notes = generate_resolved_tickets_corpus(tickets_df, num_resolutions=25)
    
    # Combine with KB articles
    knowledge_corpus = {
        "resolution_notes": resolution_notes,
        "kb_articles": KB_ARTICLES,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_resolutions": len(resolution_notes),
            "total_kb_articles": len(KB_ARTICLES),
            "categories_covered": list(set([r['category'] for r in resolution_notes]))
        }
    }
    
    # Save as JSON
    with open("data/knowledge_corpus.json", "w") as f:
        json.dump(knowledge_corpus, f, indent=2)
    
    print(f"Knowledge corpus generated:")
    print(f"  - {len(resolution_notes)} resolution notes")
    print(f"  - {len(KB_ARTICLES)} KB articles")
    print(f"  - Categories: {knowledge_corpus['metadata']['categories_covered']}")
    
    return knowledge_corpus

if __name__ == "__main__":
    corpus = save_knowledge_corpus()
