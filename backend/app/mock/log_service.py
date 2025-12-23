"""
Mock Log Service for Issue Solver Agent
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from app.mock.schemas import LogEntry, LogQueryParams, LogQueryResult

logger = logging.getLogger(__name__)

# Scenario data directory
SCENARIOS_DIR = Path(__file__).parent / "data" / "scenarios"

# Service to scenario mapping
SERVICE_SCENARIO_MAP = {
    "PaymentService": ["s1_integration_timeout.json", "s4_complex_error.json"],
    "RefundService": ["s2_code_npe.json"],
    "OrderService": ["s3_business_ux.json"],
    "MainService": ["s5_insufficient_logs.json"],
}


class MockLogService:
    """Service for querying mock logs"""

    def __init__(self):
        """Initialize mock log service"""
        self._logs_cache: dict[str, List[LogEntry]] = {}
        self._load_scenarios()

    def _load_scenarios(self) -> None:
        """Load all scenario files into cache"""
        if not SCENARIOS_DIR.exists():
            logger.warning(f"Scenarios directory not found: {SCENARIOS_DIR}")
            return

        for scenario_file in SCENARIOS_DIR.glob("*.json"):
            try:
                with open(scenario_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    service = data.get("service")
                    logs_data = data.get("logs", [])

                    # Parse logs
                    logs = []
                    for log_data in logs_data:
                        # Convert timestamp string to datetime
                        log_data["timestamp"] = datetime.fromisoformat(
                            log_data["timestamp"].replace("Z", "+00:00")
                        )
                        log = LogEntry(**log_data)
                        logs.append(log)

                    # Cache by service
                    if service:
                        if service not in self._logs_cache:
                            self._logs_cache[service] = []
                        self._logs_cache[service].extend(logs)

                logger.info(f"Loaded scenario: {scenario_file.name} ({len(logs)} logs)")

            except Exception as e:
                logger.error(f"Failed to load scenario {scenario_file}: {e}")

    def query_logs(self, params: LogQueryParams) -> LogQueryResult:
        """
        Query mock logs

        Args:
            params: Query parameters

        Returns:
            Query result with logs
        """
        # Get logs for service
        all_logs = self._logs_cache.get(params.service, [])

        if not all_logs:
            logger.warning(f"No logs found for service: {params.service}")
            return LogQueryResult(logs=[], total_count=0, filtered_count=0)

        # Ensure timezone aware comparison
        start_time = params.start_time
        end_time = params.end_time
        if start_time.tzinfo is None:
            from datetime import timezone
            start_time = start_time.replace(tzinfo=timezone.utc)
            end_time = end_time.replace(tzinfo=timezone.utc)

        # Filter by time range
        filtered_logs = [
            log for log in all_logs
            if start_time <= log.timestamp <= end_time
        ]

        # Filter by level if specified
        if params.level:
            filtered_logs = [
                log for log in filtered_logs
                if log.level == params.level
            ]

        total_count = len(filtered_logs)

        # Apply limit
        limited_logs = filtered_logs[:params.limit]

        logger.info(
            f"Query: service={params.service}, "
            f"time_range={params.start_time} ~ {params.end_time}, "
            f"level={params.level}, "
            f"total={total_count}, filtered={len(limited_logs)}"
        )

        return LogQueryResult(
            logs=limited_logs,
            total_count=total_count,
            filtered_count=len(limited_logs)
        )

    def get_available_services(self) -> List[str]:
        """Get list of available services"""
        return list(self._logs_cache.keys())

    def get_log_count_by_service(self, service: str) -> int:
        """Get total log count for a service"""
        return len(self._logs_cache.get(service, []))


_mock_log_service_instance: Optional[MockLogService] = None


def get_mock_log_service() -> MockLogService:
    """Get singleton mock log service instance"""
    global _mock_log_service_instance
    if _mock_log_service_instance is None:
        _mock_log_service_instance = MockLogService()
    return _mock_log_service_instance
