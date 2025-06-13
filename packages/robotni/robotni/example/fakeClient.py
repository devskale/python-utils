import time
import uuid
import random
import threading
import queue
import requests

class FakeClient:
    def __init__(self, api_base_url="http://localhost:8000", interval=5, poll_interval=1):
        self.api_base_url = api_base_url
        self.interval = interval  # Interval to send new job requests
        self.poll_interval = poll_interval  # Interval to poll job status
        self.jobs = {}  # Stores job_id: {'status': 'pending', 'result': None}
        self.running = False
        self.job_sender_thread = None
        self.job_poller_thread = None
        self.job_queue = queue.Queue() # Queue for jobs to be processed

    def _get_job_types(self):
        """Fetches available job types from the API."""
        try:
            response = requests.get(f"{self.api_base_url}/api/worker/types")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[Client] Error fetching job types: {e}")
            return {}

    def _send_job_request(self):
        """Sends a job request to the API."""
        job_types = self._get_job_types()
        job_type = "fakejob" if "fakejob" in job_types else list(job_types.keys())[0] if job_types else "fakejob"
        delay_seconds = random.randint(1, 10) # Random delay for the fake job
        payload = {"type": job_type, "params": {"delay_seconds": delay_seconds}}
        try:
            response = requests.post(f"{self.api_base_url}/api/worker/jobs", json=payload)
            response.raise_for_status()
            job_data = response.json()
            job_id = job_data["job_id"]
            self.jobs[job_id] = {'status': 'queued', 'type': job_type, 'params': payload['params'], 'result': None, 'error': None}
            print(f"[Client] Sent job request: {job_id} (Type: {job_type}, Delay: {delay_seconds}s)")
            return job_id
        except requests.exceptions.RequestException as e:
            print(f"[Client] Error sending job request: {e}")
            return None

    def _poll_job_status(self, job_id):
        """Polls the status of a job from the API."""
        try:
            response = requests.get(f"{self.api_base_url}/api/worker/jobs/{job_id}")
            response.raise_for_status()
            job_status = response.json()
            # Update local job status
            if job_id in self.jobs:
                self.jobs[job_id].update(job_status)
                print(f"[Client] Polled job {job_id}: Status: {job_status['status']}")
                if job_status['status'] in ["done", "failed"]:
                    return True # Job is complete
            return False # Job is not complete
        except requests.exceptions.RequestException as e:
            print(f"[Client] Error polling job {job_id}: {e}")
            return False

    def _job_sender_loop(self):
        """Periodically sends job requests."""
        while self.running:
            self._send_job_request()
            time.sleep(self.interval)

    def _job_poller_loop(self):
        """Periodically polls job statuses."""
        while self.running or any(job['status'] not in ["done", "failed"] for job in self.jobs.values()):
            jobs_to_poll = [job_id for job_id, details in self.jobs.items() if details['status'] not in ["done", "failed"]]
            for job_id in jobs_to_poll:
                self._poll_job_status(job_id)
            time.sleep(self.poll_interval)

    def start(self):
        """Starts the fake client, sending and polling jobs."""
        if self.running:
            print("Client is already running.")
            return

        self.running = True
        print("Starting fake client...")

        self.job_sender_thread = threading.Thread(target=self._job_sender_loop)
        self.job_sender_thread.daemon = True
        self.job_sender_thread.start()

        self.job_poller_thread = threading.Thread(target=self._job_poller_loop)
        self.job_poller_thread.daemon = True
        self.job_poller_thread.start()

        print("Fake client started. Press Ctrl+C to interrupt.")

    def stop(self):
        """Stops the fake client."""
        if not self.running:
            print("Client is not running.")
            return

        print("Stopping fake client...")
        self.running = False

        if self.job_sender_thread and self.job_sender_thread.is_alive():
            self.job_sender_thread.join(timeout=self.interval + 1)

        if self.job_poller_thread and self.job_poller_thread.is_alive():
            # Wait for the poller to finish processing remaining jobs
            self.job_poller_thread.join(timeout=self.poll_interval + 1)

        print("Fake client stopped.")
        self._report_final_status()

    def _report_final_status(self):
        """Reports the final status of all jobs."""
        print("\n--- Final Job Status Report ---")
        if not self.jobs:
            print("No jobs were processed.")
            return

        for job_id, details in self.jobs.items():
            print(f"Job ID: {job_id}, Type: {details.get('type', 'N/A')}, Status: {details['status']}, Result: {details.get('result', 'N/A')}, Error: {details.get('error', 'N/A')}")
        print("-------------------------------")

if __name__ == "__main__":
    client = FakeClient(interval=3, poll_interval=1)
    try:
        client.start()
        while client.running:
            time.sleep(1) # Keep main thread alive
    except KeyboardInterrupt:
        print("\nInterruption detected. Stopping client...")
    finally:
        client.stop()
