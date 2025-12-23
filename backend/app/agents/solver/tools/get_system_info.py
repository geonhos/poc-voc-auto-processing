"""
get_system_info tool - Get system information
"""

import logging
from typing import Optional

from app.agents.solver.tools.schemas import GetSystemInfoInput, GetSystemInfoOutput

logger = logging.getLogger(__name__)

# Mock system information database
SYSTEM_INFO_DB = {
    "PaymentGateway": {
        "type": "external",
        "contact_info": "partner-support@paymentgateway.com",
        "recent_incidents": [
            "2024-01-10: API 응답 시간 증가 (해결됨)",
            "2024-01-05: 임시 서비스 중단 30분"
        ]
    },
    "PaymentService": {
        "type": "internal",
        "contact_info": "backend-team@company.com",
        "recent_incidents": []
    },
    "RefundService": {
        "type": "internal",
        "contact_info": "backend-team@company.com",
        "recent_incidents": []
    },
    "OrderService": {
        "type": "internal",
        "contact_info": "backend-team@company.com",
        "recent_incidents": []
    },
    "MainService": {
        "type": "internal",
        "contact_info": "backend-team@company.com",
        "recent_incidents": []
    },
    "EmailService": {
        "type": "external",
        "contact_info": "support@emailprovider.com",
        "recent_incidents": []
    },
    "ShippingAPI": {
        "type": "external",
        "contact_info": "api-support@shipping.com",
        "recent_incidents": []
    }
}


def get_system_info(system_name: str) -> GetSystemInfoOutput:
    """
    Get system information

    Args:
        system_name: Name of the system to query

    Returns:
        GetSystemInfoOutput with system information
    """
    try:
        # Validate input
        input_data = GetSystemInfoInput(system_name=system_name)

        # Look up system info
        info = SYSTEM_INFO_DB.get(input_data.system_name)

        if not info:
            # Unknown system - assume internal
            logger.warning(f"System not found in database: {system_name}, assuming internal")
            return GetSystemInfoOutput(
                system_name=input_data.system_name,
                type="internal",
                contact_info=None,
                recent_incidents=[]
            )

        logger.info(f"Retrieved system info for: {system_name} (type: {info['type']})")

        return GetSystemInfoOutput(
            system_name=input_data.system_name,
            type=info["type"],
            contact_info=info.get("contact_info"),
            recent_incidents=info.get("recent_incidents", [])
        )

    except Exception as e:
        logger.error(f"Error in get_system_info tool: {e}")
        return GetSystemInfoOutput(
            system_name=system_name,
            type="unknown",
            contact_info=None,
            recent_incidents=[]
        )
