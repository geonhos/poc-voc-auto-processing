"""
analyze_error_patterns tool - Analyze error patterns in logs
"""

import logging
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any

from app.agents.solver.tools.schemas import (
    AnalyzeErrorPatternsInput,
    AnalyzeErrorPatternsOutput,
    ErrorSummary,
    ExternalSystemError
)

logger = logging.getLogger(__name__)


def analyze_error_patterns(logs: List[Dict[str, Any]]) -> AnalyzeErrorPatternsOutput:
    """
    Analyze error patterns in log entries

    Args:
        logs: List of log entries (dicts)

    Returns:
        AnalyzeErrorPatternsOutput with error analysis
    """
    try:
        # Validate input
        input_data = AnalyzeErrorPatternsInput(logs=logs)

        # Initialize counters
        error_by_code = defaultdict(list)
        stack_traces = []
        external_errors = defaultdict(int)
        total_errors = 0
        total_warnings = 0

        # Analyze each log
        for log in input_data.logs:
            level = log.get("level", "")
            error_code = log.get("error_code")
            stack_trace = log.get("stack_trace")
            message = log.get("message", "")
            timestamp_str = log.get("timestamp", "")
            metadata = log.get("metadata", {})

            # Count by level
            if level == "ERROR":
                total_errors += 1
            elif level == "WARN":
                total_warnings += 1

            # Group by error code
            if error_code and level == "ERROR":
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.now()

                error_by_code[error_code].append({
                    "timestamp": timestamp,
                    "message": message,
                    "metadata": metadata
                })

            # Collect stack traces
            if stack_trace:
                # Extract main error line
                lines = stack_trace.split("\n")
                if lines:
                    stack_traces.append(lines[0].strip())

            # Detect external system errors
            if "external" in message.lower() or "gateway" in message.lower():
                gateway = metadata.get("gateway")
                if gateway:
                    external_errors[gateway] += 1

        # Create error summaries
        error_summaries = []
        for error_code, occurrences in error_by_code.items():
            if not occurrences:
                continue

            timestamps = [occ["timestamp"] for occ in occurrences]
            error_summaries.append(ErrorSummary(
                error_code=error_code,
                count=len(occurrences),
                first_occurrence=min(timestamps),
                last_occurrence=max(timestamps),
                sample_message=occurrences[0]["message"]
            ))

        # Sort by count descending
        error_summaries.sort(key=lambda x: x.count, reverse=True)

        # Get unique stack trace patterns
        unique_stack_traces = list(set(stack_traces))[:10]  # Top 10

        # Create external system error list
        external_system_errors = [
            ExternalSystemError(system=system, error_count=count)
            for system, count in external_errors.items()
        ]
        external_system_errors.sort(key=lambda x: x.error_count, reverse=True)

        logger.info(
            f"Analyzed {len(input_data.logs)} logs: "
            f"{total_errors} errors, {total_warnings} warnings, "
            f"{len(error_summaries)} unique error codes"
        )

        return AnalyzeErrorPatternsOutput(
            error_summary=error_summaries,
            stack_trace_patterns=unique_stack_traces,
            external_system_errors=external_system_errors,
            total_errors=total_errors,
            total_warnings=total_warnings
        )

    except Exception as e:
        logger.error(f"Error in analyze_error_patterns tool: {e}")
        return AnalyzeErrorPatternsOutput()
