# a job that idles for a while

import time
import random


def run_fakejob(delay_seconds=5):
    """Simulate a fake job by sleeping for a random time up to delay_seconds."""
    waited = random.randint(1, delay_seconds)
    print(f"FakeJob: waiting for {waited} seconds...")
    time.sleep(waited)
    print("FakeJob: done.")
    return {"waited": waited}


if __name__ == "__main__":
    # Example usage for manual testing
    result = run_fakejob(5)
    print(f"Result: {result}")
