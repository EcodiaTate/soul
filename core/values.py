# core/values.py

from core.db import get_session

def get_active_values():
    with get_session() as session:
        result = session.run("""
            MATCH (v:Value {active: true})
            RETURN v.name AS name, v.weight AS weight
            ORDER BY v.order
        """)
        return [r["name"] for r in result]
