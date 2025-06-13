from .tasks import run_named_task


def submit_job(job_id, name, params):
    """
    Submit a job to the task queue

    Args:
        job_id (str): Unique identifier for the job
        name (str): Name of the task to execute
        params (dict): Parameters for the task

    Returns:
        None
    """
    # Queue the task for async execution
    run_named_task.schedule(
        args=(job_id, name, params),
        delay=0
    )
    return job_id
