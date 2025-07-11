# actuators/all_outputs.py

import logging

logging.basicConfig(level=logging.INFO, filename="logs/all_outputs.log")

# List your action handlers — just add more as you expand
ACTION_HANDLERS = [
    "actuators.write_gsheet",
    "actuators.send_email",
    "actuators.write_wp",
    "actuators.cypher_exec",
    # "actuators.trigger_device",
    # Add your own handlers here
]

def execute_action(action_plan):
    """Dispatch action plans to all appropriate output handlers."""
    results = []
    for handler_mod in ACTION_HANDLERS:
        try:
            mod = __import__(handler_mod, fromlist=['handle_action'])
            if hasattr(mod, "handle_action"):
                result = mod.handle_action(action_plan)
                results.append(result)
                logging.info(f"Action handled by {handler_mod}: {result}")
            else:
                logging.warning(f"{handler_mod} has no handle_action()")
        except Exception as e:
            logging.error(f"Error in {handler_mod}: {e}")
    return results

# === Example for standalone test ===
if __name__ == "__main__":
    sample_plan = {
        "event_id": 1,
        "actions": ["Send a summary email", "Write a WP post"],
        "source": "test"
    }
    execute_action(sample_plan)
