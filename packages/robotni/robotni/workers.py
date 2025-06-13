import random
import time
from typing import Dict, Any, Tuple, Callable

def process_fakejob(params: Dict[str, Any], job_id: str = "", update_status: Callable[[str, str], None] = None) -> Tuple[Dict[str, Any], str]:
    """
    Process a fake job by simulating stages: operational for a few seconds before completion.
    
    Args:
        params: Dictionary containing job parameters.
               Expected key: 'delay_seconds' (int, optional, default=5)
        job_id: The ID of the job being processed (for status updates).
        update_status: Function to update job status in storage (takes job_id, status as arguments).
    
    Returns:
        Tuple of (result_dict, error_message). If successful, error_message is empty.
    """
    delay_seconds = params.get("delay_seconds", 5)
    if not isinstance(delay_seconds, int) or delay_seconds < 1:
        return {}, "delay_seconds must be a positive integer"
    
    # Simulate queued stage (already handled by API, but ensure visibility)
    if update_status and job_id:
        update_status(job_id, "queued")
    time.sleep(1)  # Short delay to simulate initial queuing
    
    # Simulate operational stage
    operational_time = max(2, delay_seconds // 2)  # Ensure operational time is at least 2 seconds
    if update_status and job_id:
        update_status(job_id, "operational")
    time.sleep(operational_time)
    
    # Simulate finishing stage
    if update_status and job_id:
        update_status(job_id, "finishing")
    time.sleep(1)  # Short delay before completion
    
    # Return result
    return {"queued_time": 1, "operational_time": operational_time, "finishing_time": 1, "total_delay": delay_seconds}, ""
