import os
import uuid
import time
import docker
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




NETWORK_NAME = os.getenv("WORKER_NETWORK", "job_net")

def init_db():
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Baza de date a fost initializata!")
            break
        except Exception as e:
            logger.error(f"DB nu e gata inca... retrying ({retries}). Error: {e}")
            retries -= 1
            time.sleep(5)


# Configurare Baza de Date
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@db:5432/jobsdb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, index=True)
    tasks = Column(JSON)
    results = Column(JSON, default=[])
    status = Column(String, default="pending") # pending, running, completed
    created_at = Column(DateTime, default=datetime.utcnow)


init_db()


app = FastAPI()
docker_client = docker.from_env()

@app.post("/jobs")
async def create_job(payload: dict):
    try:
        job_id = str(uuid.uuid4())
        logger.info(f"Incepere creare job: {job_id}")
        
        db_session = SessionLocal()
        # Verificam daca DB e accesibila
        new_job = Job(id=job_id, tasks=payload["tasks"], status="pending")
        db_session.add(new_job)
        db_session.commit()
        db_session.close()
        
        logger.info("Job salvat in DB. Incerc lansare container...")

        docker_client.services.create(
            image="job-worker:latest",
            name=f"job-{job_id}",
            networks=[NETWORK_NAME],
            env=[
                f"JOB_ID={job_id}",
                f"DATABASE_URL={DATABASE_URL}"
            ],
            restart_policy={"Condition": "none"} # Atentie la formatul SDK-ului
        )
        
        logger.info(f"Serviciu job-{job_id} creat cu succes.")
        return {"job_id": job_id}

    except Exception as e:
        logger.error(f"EROARE CRITICA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    db.close()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "tasks": job.tasks,
        "results": job.results
    }