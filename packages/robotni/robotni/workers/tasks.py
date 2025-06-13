from huey import SqliteHuey
import subprocess

huey = SqliteHuey(filename='robotni.db')


@huey.task(expires=3600)
def run_python_script(job_id, script_path, venv_path, job_type, project):
    # Run the script in the specified venv using subprocess
    python_bin = f"{venv_path}/bin/python"
    try:
        result = subprocess.run(
            [python_bin, script_path],
            capture_output=True,
            text=True,
            timeout=3600
        )
        # Store result/output as needed
        return {
            "jobId": job_id,
            "status": "completed" if result.returncode == 0 else "failed",
            "output": result.stdout + result.stderr,
            "type": job_type,
            "project": project,
        }
    except subprocess.TimeoutExpired:
        return {
            "jobId": job_id,
            "status": "timeout",
            "output": None,
            "type": job_type,
            "project": project,
        }
    except Exception as e:
        return {
            "jobId": job_id,
            "status": "error",
            "output": str(e),
            "type": job_type,
            "project": project,
        }


@huey.task(expires=3600)
def run_named_task(job_id, name, params):
    # Example: just echo the input for now
    return {
        "jobId": job_id,
        "status": "completed",
        "output": f"Ran task '{name}' with params {params}",
        "type": name,
        "params": params,
    }
