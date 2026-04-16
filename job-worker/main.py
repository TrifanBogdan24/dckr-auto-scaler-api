import os
import time
import random
import json
from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
JOB_ID = os.getenv("JOB_ID")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    tasks = Column(JSON)
    results = Column(JSON)
    status = Column(String)

def process_job():
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == JOB_ID).first()
    
    if not job:
        print(f"Job {JOB_ID} nu a fost gasit.")
        return

    # Update status la running
    job.status = "running"
    db.commit()

    results = []
    for task in job.tasks:
        min_val, max_val = task
        # Generare numar random
        res_val = random.randint(min_val, max_val)
        # Sleep pentru durata in ms (res_val folosit ca durata conform logicii tale)
        time.sleep(res_val / 1000.0)
        results.append(res_val)

    # Finalizare
    job.results = results
    job.status = "completed"
    db.commit()
    db.close()
    print(f"Job {JOB_ID} finalizat cu succes.")

if __name__ == "__main__":
    if JOB_ID:
        process_job()
