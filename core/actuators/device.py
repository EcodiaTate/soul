# /core/actuators/dispatch.py
def dispatch_actuator(action_plan):
    action_type = action_plan["action_type"]
    if action_type == "email":
        from .email import execute
    elif action_type == "gsheet":
        from .gsheet import execute
    elif action_type == "webhook":
        from .webhook import execute
    else:
        return {"status": "error", "details": "Unknown action type"}
    return execute(action_plan)