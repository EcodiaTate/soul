import time
import json

class MemoryManager:
    def __init__(self, decay_time_days=30):
        self.decay_time = decay_time_days * 86400  # seconds
        self.archive_path = "logs/memory_archive.json"

    def decay(self, memories):
        now = time.time()
        survived, archived = [], []
        for mem in memories:
            mem_time = time.mktime(time.strptime(mem["timestamp"], "%Y-%m-%dT%H:%M:%S.%f"))
            if now - mem_time > self.decay_time:
                archived.append(mem)
            else:
                survived.append(mem)
        if archived:
            with open(self.archive_path, "a", encoding="utf-8") as f:
                for mem in archived:
                    f.write(json.dumps(mem) + "\n")
        return survived

    def recall(self, memories, n=5):
        # Simple: return n most recent; could expand with vector or impact search
        return sorted(memories, key=lambda m: m["timestamp"], reverse=True)[:n]
