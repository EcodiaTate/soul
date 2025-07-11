import threading
import time
from pipeline.living_world_brain import EcodiaWorldSoul

def run_pipeline_cycle():
    soul = EcodiaWorldSoul()
    while True:
        t1 = threading.Thread(target=soul.full_cycle)
        t1.start()
        t1.join(timeout=180)  # cycle time
        time.sleep(10)

if __name__ == "__main__":
    run_pipeline_cycle()
