# /core/actuators/email.py
def execute(action_plan):
    # Validate action_plan["params"]
    # Use smtplib to send email
    # Return {"status": "success", "details": "..."} or error dict