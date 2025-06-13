import time

def taskFakejob():
    time.sleep(5)  # Simulate a delay
    msg = "Fake job completed"
    print(msg)
    return msg
