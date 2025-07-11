# pipeline/orchestrator.py

import subprocess
import time

CYCLES = [
    "pipeline/data_ingest.py",
    "pipeline/living_world_brain.py",
    "pipeline/peer_review.py",
    "pipeline/judge.py",
    "pipeline/consciousness_engine.py",
    "pipeline/decay.py",
    "pipeline/self_audit.py",
]

def run_all_cycles():
    for script in CYCLES:
        print(f"\n=== Running {script} ===\n")
        subprocess.run(["python", script])
        time.sleep(1)  # Pause to reduce resource collisions

if __name__ == "__main__":
    run_all_cycles()
