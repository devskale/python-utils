# a job that idles for a while

import time
import random


def run_fakejob(delay_seconds=5):
    """Simulate a fake job by faking work for a random time up to delay_seconds."""
    waited = random.randint(1, delay_seconds)
    print(f"FakeJob: Faking work for {waited} seconds...")
    start = time.time()
    time.sleep(waited)
    end = time.time()
    runtime = round(end - start, 3)
    print("FakeJob: done.")
    return {"waited": waited, "runtime": runtime}


if __name__ == "__main__":
    # Example usage for manual testing
    result = run_fakejob(5)
    print(f"Result: {result}")
