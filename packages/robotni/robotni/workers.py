import random
import time
from typing import Dict, Any, Tuple

def process_fakejob(params: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """
    Process a fake job by waiting a random amount of time between 1 second
    and the specified delay_seconds parameter (default 5).
    
    Args:
        params: Dictionary containing job parameters.
               Expected key: 'delay_seconds' (int, optional, default=5)
    
    Returns:
        Tuple of (result_dict, error_message). If successful, error_message is empty.
    """
    delay_seconds = params.get("delay_seconds", 5)
    if not isinstance(delay_seconds, int) or delay_seconds < 1:
        return {}, "delay_seconds must be a positive integer"
    
    # Generate random delay between 1 and delay_seconds
    wait_time = random.randint(1, delay_seconds)
    
    # Simulate work by sleeping
    time.sleep(wait_time)
    
    # Return result
    return {"waited": wait_time}, ""
