"""
Solver Agent Implementation
"""

import json
import re
import logging
from typing import Optional
from datetime import datetime, timedelta
import asyncio

from app.agents.solver.schemas import (
    SolverAgentInput,
    SolverAgentOutput,
    ConfidenceScore,
    ActionProposal,
)
from app.agents.solver.prompts import SYSTEM_PROMPT, format_user_prompt
from app.agents.solver.tools import (
    get_logs,
    analyze_error_patterns,
    get_system_info,
    search_similar_vocs,
)
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class SolverAgent:
    """Solver Agent for analyzing VOC issues and proposing solutions"""

    def __init__(self):
        """Initialize solver agent"""
        self.llm_service = get_llm_service()
        self.timeout = 120  # 120 seconds timeout for complex analysis

    async def solve(self, input_data: SolverAgentInput) -> SolverAgentOutput:
        """
        Analyze VOC issue and propose solution

        Args:
            input_data: VOC input with ticket_id, raw_voc, received_at

        Returns:
            Solver analysis output with problem type, confidence, and action
        """
        try:
            # Step 1: Gather data using tools
            logger.info(f"Starting analysis for ticket: {input_data.ticket_id}")
            tool_data = await self._gather_tool_data(input_data)

            # Step 2: Format comprehensive prompt with tool data
            analysis_prompt = self._format_analysis_prompt(input_data, tool_data)

            # Step 3: Call LLM for analysis with timeout
            logger.info(f"Calling LLM for analysis: {input_data.ticket_id}")
            response = await asyncio.wait_for(
                self.llm_service.generate_json(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=analysis_prompt,
                    temperature=0.1,
                ),
                timeout=self.timeout,
            )

            # Step 4: Parse and structure response
            output = self._parse_response(input_data.ticket_id, response)

            if output is None:
                # Fallback: create minimal output if parsing fails
                logger.warning(f"Failed to parse LLM response for {input_data.ticket_id}, using fallback")
                return self._create_fallback_output(input_data)

            logger.info(f"Analysis completed for {input_data.ticket_id}: {output.problem_type_primary}, confidence={output.confidence.overall:.2f}")
            return output

        except asyncio.TimeoutError:
            logger.error(f"Analysis timeout for {input_data.ticket_id}")
            return self._create_fallback_output(input_data, error="TIMEOUT")

        except Exception as e:
            logger.error(f"Error analyzing {input_data.ticket_id}: {e}")
            return self._create_fallback_output(input_data, error=str(e))

    async def _gather_tool_data(self, input_data: SolverAgentInput) -> dict:
        """
        Gather data from all available tools

        Args:
            input_data: VOC input

        Returns:
            Dictionary with tool results
        """
        # Calculate time window for log query (1 hour before and after)
        start_time = input_data.received_at - timedelta(hours=1)
        end_time = input_data.received_at + timedelta(hours=1)

        # Try to infer service name from VOC content (simple heuristic)
        service = self._infer_service_name(input_data.raw_voc)

        # 1. Get logs
        logger.info(f"Fetching logs for service: {service}")
        log_result = get_logs(
            service=service,
            start_time=start_time,
            end_time=end_time,
            level="ERROR",
            limit=100
        )

        # 2. Analyze error patterns
        error_analysis = None
        if log_result.logs:
            logger.info(f"Analyzing {len(log_result.logs)} log entries")
            error_analysis = analyze_error_patterns(log_result.logs)

        # 3. Search similar VOCs
        logger.info(f"Searching similar VOC cases")
        similar_cases = search_similar_vocs(
            query=input_data.raw_voc,
            top_k=5,
            min_similarity=0.5
        )

        # 4. Get system info if a system is mentioned
        system_info = None
        if error_analysis and error_analysis.external_system_errors:
            # Get info for the most problematic external system
            system_name = error_analysis.external_system_errors[0].system
            logger.info(f"Fetching system info for: {system_name}")
            system_info = get_system_info(system_name)

        return {
            "logs": log_result.logs,
            "log_count": log_result.total_count,
            "error_analysis": error_analysis,
            "similar_cases": similar_cases.similar_cases,
            "system_info": system_info,
            "inferred_service": service,
        }

    def _infer_service_name(self, raw_voc: str) -> str:
        """
        Infer service name from VOC content

        Args:
            raw_voc: Raw VOC text

        Returns:
            Service name (defaults to "MainService")
        """
        voc_lower = raw_voc.lower()

        # Simple keyword matching
        if "결제" in raw_voc or "payment" in voc_lower:
            return "PaymentService"
        elif "환불" in raw_voc or "refund" in voc_lower:
            return "RefundService"
        elif "주문" in raw_voc or "order" in voc_lower:
            return "OrderService"
        elif "이메일" in raw_voc or "email" in voc_lower:
            return "EmailService"
        else:
            return "MainService"

    def _format_analysis_prompt(self, input_data: SolverAgentInput, tool_data: dict) -> str:
        """
        Format comprehensive analysis prompt with tool data

        Args:
            input_data: VOC input
            tool_data: Gathered tool data

        Returns:
            Formatted prompt string
        """
        # Format similar cases
        similar_cases_text = ""
        if tool_data["similar_cases"]:
            similar_cases_text = "\n**Similar Historical Cases:**\n"
            for i, case in enumerate(tool_data["similar_cases"][:3], 1):
                similar_cases_text += f"{i}. Ticket {case.ticket_id} (similarity: {case.similarity_score:.2f})\n"
                similar_cases_text += f"   - Type: {case.problem_type_primary}"
                if case.problem_type_secondary:
                    similar_cases_text += f" > {case.problem_type_secondary}"
                similar_cases_text += f"\n   - Resolution: {case.resolution}\n"
        else:
            similar_cases_text = "\n**Similar Historical Cases:** None found\n"

        # Format error analysis
        error_summary_text = ""
        if tool_data["error_analysis"]:
            ea = tool_data["error_analysis"]
            error_summary_text = f"\n**Error Analysis:**\n"
            error_summary_text += f"- Total Errors: {ea.total_errors}, Warnings: {ea.total_warnings}\n"

            if ea.error_summary:
                error_summary_text += f"- Top Error Codes:\n"
                for err in ea.error_summary[:3]:
                    error_summary_text += f"  * {err.error_code}: {err.count} occurrences\n"
                    error_summary_text += f"    Sample: {err.sample_message[:100]}\n"

            if ea.external_system_errors:
                error_summary_text += f"- External System Issues:\n"
                for ext in ea.external_system_errors:
                    error_summary_text += f"  * {ext.system}: {ext.error_count} errors\n"
        else:
            error_summary_text = f"\n**Error Analysis:** No errors found in logs (checked {tool_data['log_count']} entries)\n"

        # Format system info
        system_info_text = ""
        if tool_data["system_info"]:
            si = tool_data["system_info"]
            system_info_text = f"\n**System Information ({si.system_name}):**\n"
            system_info_text += f"- Type: {si.type}\n"
            if si.contact_info:
                system_info_text += f"- Contact: {si.contact_info}\n"
            if si.recent_incidents:
                system_info_text += f"- Recent Incidents:\n"
                for incident in si.recent_incidents:
                    system_info_text += f"  * {incident}\n"

        # Combine everything
        comprehensive_prompt = f"""Analyze the following VOC issue using the gathered evidence.

**Ticket ID**: {input_data.ticket_id}
**Received At**: {input_data.received_at.isoformat()}
**Inferred Service**: {tool_data['inferred_service']}

**VOC Content**:
{input_data.raw_voc}

---
{similar_cases_text}
{error_summary_text}
{system_info_text}

---

Based on the evidence above, provide ONLY a valid JSON object (no markdown, no explanation) with this exact structure:

EXAMPLE FORMAT:
{{
  "problem_type_primary": "integration_error",
  "problem_type_secondary": "timeout",
  "affected_system": "PaymentService",
  "root_cause_analysis": "The payment gateway timed out after 5 seconds...",
  "evidence_summary": "Found 3 ERROR logs showing EXTERNAL_TIMEOUT...",
  "confidence": {{
    "error_pattern_clarity": 0.8,
    "log_voc_correlation": 0.7,
    "similar_case_match": 0.6,
    "system_info_availability": 0.9,
    "overall": 0.75
  }},
  "state": "WAITING_CONFIRM",
  "action_proposal": {{
    "action_type": "integration_inquiry",
    "title": "Contact Payment Gateway Team",
    "description": "Reach out to the payment gateway support to investigate...",
    "target_system": "PaymentGateway",
    "contact_info": "support@paymentgateway.com"
  }},
  "similar_cases_used": ["VOC-2024-001"],
  "log_summary": "3 errors between 14:28-14:32"
}}

IMPORTANT RULES:
1. problem_type_primary: MUST be exactly one of: "integration_error", "code_error", "business_improvement"
2. action_type: MUST match problem type (integration_error→integration_inquiry, code_error→code_fix, business_improvement→business_proposal)
3. All text fields (root_cause_analysis, evidence_summary, description) must be STRINGS, not lists
4. confidence scores: all numbers between 0.0 and 1.0
5. overall confidence >= 0.7 → state = "WAITING_CONFIRM", otherwise "MANUAL_REQUIRED"
6. Return ONLY the JSON object, no markdown code blocks, no extra text

YOUR RESPONSE (JSON only):
"""
        return comprehensive_prompt

    def _parse_response(self, ticket_id: str, response: str) -> Optional[SolverAgentOutput]:
        """
        Parse LLM JSON response to SolverAgentOutput

        Args:
            ticket_id: Ticket ID
            response: Raw LLM response

        Returns:
            Parsed SolverAgentOutput or None if parsing fails
        """
        try:
            # Remove markdown code blocks if present
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()

            # Extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", response_clean)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_clean

            # Parse JSON
            data = json.loads(json_str)

            # Ensure ticket_id is included
            data["ticket_id"] = ticket_id
            data["analyzed_at"] = datetime.now()

            # Fix common issues
            # If evidence_summary is a list, convert to string
            if isinstance(data.get("evidence_summary"), list):
                data["evidence_summary"] = " ".join(str(item) for item in data["evidence_summary"])

            # If root_cause_analysis is a list, convert to string
            if isinstance(data.get("root_cause_analysis"), list):
                data["root_cause_analysis"] = " ".join(str(item) for item in data["root_cause_analysis"])

            # Validate and create output
            output = SolverAgentOutput.model_validate(data)

            return output

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response was: {response[:500]}")
            return None

    def _create_fallback_output(
        self,
        input_data: SolverAgentInput,
        error: Optional[str] = None
    ) -> SolverAgentOutput:
        """
        Create fallback output when analysis fails

        Args:
            input_data: Original input
            error: Optional error message

        Returns:
            Minimal SolverAgentOutput with MANUAL_REQUIRED state
        """
        error_msg = f"분석 실패: {error}" if error else "분석 실패"

        return SolverAgentOutput(
            ticket_id=input_data.ticket_id,
            problem_type_primary="business_improvement",  # Safe default
            root_cause_analysis=f"자동 분석에 실패했습니다. {error_msg}",
            evidence_summary="충분한 증거를 수집하지 못했습니다.",
            confidence=ConfidenceScore(
                overall=0.0,
                error_pattern_clarity=0.0,
                log_voc_correlation=0.0,
                similar_case_match=0.0,
                system_info_availability=0.0,
            ),
            state="MANUAL_REQUIRED",
            action_proposal=ActionProposal(
                action_type="business_proposal",
                title="수동 분석 필요",
                description="자동 분석이 실패했습니다. 담당자가 수동으로 확인해주세요.",
            ),
        )


# Singleton instance
_solver_agent: Optional[SolverAgent] = None


def get_solver_agent() -> SolverAgent:
    """Get singleton Solver Agent instance"""
    global _solver_agent
    if _solver_agent is None:
        _solver_agent = SolverAgent()
    return _solver_agent
