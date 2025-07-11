from core.db import get_session

def get_event_by_id(event_id):
    with get_session() as session:
        result = session.run("MATCH (e:Event) WHERE id(e) = $eid RETURN e", eid=event_id)
        rec = result.single()
        return rec["e"] if rec else None
