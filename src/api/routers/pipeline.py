import threading
import uuid

from fastapi import APIRouter, HTTPException

from src.api.schemas import JobResponse, JobStatus

router = APIRouter(prefix="/pipeline")

_jobs: dict = {}


def _run_job(job_id: str, fn, *args) -> None:
    _jobs[job_id].status = JobStatus.running
    try:
        result = fn(*args)
        _jobs[job_id].status = JobStatus.done
        _jobs[job_id].result = result
    except Exception as exc:
        _jobs[job_id].status = JobStatus.failed
        _jobs[job_id].error = str(exc)


def _submit(fn, *args) -> JobResponse:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = JobResponse(job_id=job_id, status=JobStatus.pending)
    threading.Thread(target=_run_job, args=(job_id, fn, *args), daemon=True).start()
    return _jobs[job_id]


@router.post("/preprocess", response_model=JobResponse)
def preprocess():
    from src.data.preprocess import build_features

    return _submit(build_features)


@router.post("/train", response_model=JobResponse)
def train():
    from src.api.dependencies import reload_explainer, reload_model
    from src.models.train_baseline import run_training

    def _train_and_reload():
        result = run_training()
        reload_model()
        reload_explainer()
        return result

    return _submit(_train_and_reload)


@router.post("/cv", response_model=JobResponse)
def cv():
    from src.models.cv_baseline import run_cv

    return _submit(run_cv)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _jobs[job_id]
