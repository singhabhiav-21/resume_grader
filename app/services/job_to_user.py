from starlette.exceptions import HTTPException
from app.conn_session import db
from app.models.job import Jobs


def check_job(job_id, user_id):
    with db() as session:
        query = session.query(Jobs).filter(Jobs.job_id == job_id).first()
        return query is not None and query.user_id == user_id


def add_job(job_id, user_id, status):
    with db() as session:
        query = Jobs(job_id=job_id, user_id=user_id, status=status)
        session.add(query)


def update_job(job_id, user_id, status):
    with db() as session:
        query = session.query(Jobs).filter(Jobs.job_id == job_id).first()
        if query:
            query.status = status
