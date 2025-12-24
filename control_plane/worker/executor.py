"""Job execution workers."""
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
import httpx

from db.models import Job, Run, RunStatus, ConnectionType


def get_trino_connection_config(connection_config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract Trino connection config from connection."""
    return {
        "endpoint": connection_config.get("endpoint", "http://trino-coordinator:8080"),
        "catalog": connection_config.get("catalog", "iceberg"),
        "schema": connection_config.get("schema", "default"),
    }


def execute_trino_sql_job(db: Session, run: Run, job: Job):
    """Execute a Trino SQL job."""
    from db.models import Connection
    
    # Update run status
    run.status = RunStatus.RUNNING
    run.started_at = datetime.utcnow()
    db.commit()
    
    try:
        # Get connection if specified
        connection = None
        if job.connection_id:
            connection = db.query(Connection).filter(Connection.id == job.connection_id).first()
            if not connection or connection.connection_type != ConnectionType.TRINO:
                raise ValueError("Invalid Trino connection")
        
        # Get Trino endpoint from connection or job definition
        if connection:
            trino_config = get_trino_connection_config(connection.config)
            trino_endpoint = trino_config["endpoint"]
        else:
            trino_endpoint = job.definition.get("endpoint", "http://trino-coordinator:8080")
        
        # Get SQL query from job definition
        sql_query = job.definition.get("sql")
        if not sql_query:
            raise ValueError("SQL query not found in job definition")
        
        # Execute query via Trino REST API
        # Note: This is a simplified implementation. In production, use a proper Trino client.
        query_url = f"{trino_endpoint}/v1/statement"
        
        # Submit query
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                query_url,
                headers={"X-Trino-User": "control-plane"},
                content=sql_query
            )
            response.raise_for_status()
            
            # Trino REST API returns query info
            query_info = response.json()
            
            # For simplicity, we'll just mark as succeeded
            # In production, poll for completion and fetch results
            run.status = RunStatus.SUCCEEDED
            run.completed_at = datetime.utcnow()
            run.result = {
                "query_id": query_info.get("id"),
                "info": query_info
            }
            db.commit()
    
    except Exception as e:
        run.status = RunStatus.FAILED
        run.completed_at = datetime.utcnow()
        run.error_message = str(e)
        db.commit()
        raise


def execute_spark_batch_job(db: Session, run: Run, job: Job):
    """Execute a Spark batch job (placeholder for future implementation)."""
    run.status = RunStatus.FAILED
    run.completed_at = datetime.utcnow()
    run.error_message = "Spark batch jobs not yet implemented"
    db.commit()
    raise NotImplementedError("Spark batch jobs not yet implemented")

