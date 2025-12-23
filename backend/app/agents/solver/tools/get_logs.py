"""
get_logs tool - Retrieve logs from mock log system
"""

import logging
from datetime import datetime

from app.agents.solver.tools.schemas import GetLogsInput, GetLogsOutput
from app.mock import get_mock_log_service
from app.mock.schemas import LogQueryParams

logger = logging.getLogger(__name__)


def get_logs(
    service: str,
    start_time: datetime,
    end_time: datetime,
    level: str = None,
    limit: int = 100
) -> GetLogsOutput:
    """
    Get logs from mock log system

    Args:
        service: Service name to query
        start_time: Start time for query
        end_time: End time for query
        level: Optional log level filter
        limit: Maximum number of logs

    Returns:
        GetLogsOutput with logs and count
    """
    try:
        # Validate input
        input_data = GetLogsInput(
            service=service,
            start_time=start_time,
            end_time=end_time,
            level=level,
            limit=limit
        )

        # Query mock log service
        log_service = get_mock_log_service()
        params = LogQueryParams(
            service=input_data.service,
            start_time=input_data.start_time,
            end_time=input_data.end_time,
            level=input_data.level,
            limit=input_data.limit
        )

        result = log_service.query_logs(params)

        # Convert to dict format
        logs_dict = [
            {
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "service": log.service,
                "message": log.message,
                "error_code": log.error_code,
                "stack_trace": log.stack_trace,
                "metadata": log.metadata
            }
            for log in result.logs
        ]

        logger.info(f"Retrieved {len(logs_dict)} logs for service: {service}")

        return GetLogsOutput(
            logs=logs_dict,
            total_count=result.total_count
        )

    except Exception as e:
        logger.error(f"Error in get_logs tool: {e}")
        return GetLogsOutput(logs=[], total_count=0)
