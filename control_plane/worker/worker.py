"""
Worker process that polls for queued runs and executes them
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.models import (
    RunStatus,
    JobType,
    init_db,
    SessionLocal,
    Run,
    Job,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Polling interval in seconds
POLL_INTERVAL = 5


class RunExecutor:
    """Executes queued runs"""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    async def execute_trino_run(self, run: Run, job: Job) -> None:
        """Execute a Trino SQL run"""
        logger.info(f"Executing Trino run {run.id} for job {job.id}")
        # TODO: Implement Trino client call
        # For now, simulate success
        db = self.db_session_factory()
        try:
            run.status = RunStatus.RUNNING.value
            run.started_at = datetime.utcnow()
            db.commit()

            # Simulate execution
            await asyncio.sleep(2)

            run.status = RunStatus.SUCCEEDED.value
            run.completed_at = datetime.utcnow()
            run.artifacts = {"query_id": f"trino-query-{run.id}"}
            db.commit()
            logger.info(f"Trino run {run.id} completed successfully")
        except Exception as e:
            logger.error(f"Trino run {run.id} failed: {e}")
            run.status = RunStatus.FAILED.value
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
        finally:
            db.close()

    async def execute_spark_run(self, run: Run, job: Job) -> None:
        """Execute a Spark batch run"""
        logger.info(f"Executing Spark run {run.id} for job {job.id}")
        # TODO: Implement Spark Operator client (create SparkApplication CR)
        # For now, simulate success
        db = self.db_session_factory()
        try:
            run.status = RunStatus.RUNNING.value
            run.started_at = datetime.utcnow()
            db.commit()

            # Simulate execution
            await asyncio.sleep(5)

            run.status = RunStatus.SUCCEEDED.value
            run.completed_at = datetime.utcnow()
            run.artifacts = {
                "spark_application_name": f"spark-app-{run.id}",
                "driver_logs": f"kubectl logs spark-app-{run.id}-driver",
            }
            db.commit()
            logger.info(f"Spark run {run.id} completed successfully")
        except Exception as e:
            logger.error(f"Spark run {run.id} failed: {e}")
            run.status = RunStatus.FAILED.value
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
        finally:
            db.close()

    async def execute_run(self, run: Run) -> None:
        """Execute a single run"""
        db = self.db_session_factory()
        try:
            job = db.query(Job).filter(Job.id == run.job_id).first()
            if not job:
                logger.error(f"Job {run.job_id} not found for run {run.id}")
                return

            if job.job_type == JobType.TRINO_SQL.value:
                await self.execute_trino_run(run, job)
            elif job.job_type == JobType.SPARK_BATCH.value:
                await self.execute_spark_run(run, job)
            else:
                logger.error(f"Unknown job type: {job.job_type}")
        finally:
            db.close()


async def worker_loop():
    """Main worker loop that polls for queued runs"""
    logger.info("Starting worker loop")

    # Initialize database
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:dev@localhost:5432/sadeem_platform"
    )
    init_db(database_url)
    db_session_factory = SessionLocal

    executor = RunExecutor(db_session_factory)

    while True:
        try:
            db = db_session_factory()
            try:
                # Fetch queued runs
                queued_runs = (
                    db.query(Run)
                    .filter(Run.status == RunStatus.QUEUED.value)
                    .limit(10)
                    .all()
                )

                if queued_runs:
                    logger.info(f"Found {len(queued_runs)} queued runs")
                    for run in queued_runs:
                        await executor.execute_run(run)
                else:
                    await asyncio.sleep(POLL_INTERVAL)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in worker loop: {e}")
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(worker_loop())

