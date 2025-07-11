from core.db import get_session
import time

def decay_old_events(age_days=90):
    cutoff = int(time.time() * 1000) - (age_days * 86400000)  # ms timestamp
    with get_session() as session:
        session.run("""
            MATCH (e:Event) WHERE e.created < $cutoff AND e.status = 'processed'
            SET e.status = 'archived'
        """, cutoff=cutoff)
    print(f"Decay run completed. All processed events older than {age_days} days archived.")

if __name__ == "__main__":
    decay_old_events()
