"""
Agentic AI Service for Server Log Analysis using Anthropic Claude.
"""

import os
import json
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
from dataclasses import dataclass

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END


@dataclass
class LogAnalysisResult:
    """Structured result from log analysis"""
    root_cause: str
    severity: str
    recommendations: List[str]
    affected_components: List[str]
    timestamp: str
    raw_analysis: str


@dataclass
class ClaudeConfig:
    """Runtime configuration for the Claude-powered agent"""
    model: str = "claude-3-sonnet-20240229"
    temperature: float = 0.2
    max_tokens_to_sample: int = 1024
    top_p: Optional[float] = None

    @classmethod
    def from_env(cls) -> "ClaudeConfig":
        model = os.getenv("CLAUDE_MODEL_NAME", cls.model)
        temperature = cls.temperature
        try:
            temperature = float(os.getenv("CLAUDE_TEMPERATURE", temperature))
        except ValueError:
            pass

        max_tokens = cls.max_tokens_to_sample
        try:
            max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", max_tokens))
        except ValueError:
            pass

        top_p_value: Optional[float] = None
        top_p_env = os.getenv("CLAUDE_TOP_P")
        if top_p_env:
            try:
                top_p_value = float(top_p_env)
            except ValueError:
                top_p_value = None

        return cls(
            model=model,
            temperature=temperature,
            max_tokens_to_sample=max_tokens,
            top_p=top_p_value
        )


class AgentState(TypedDict, total=False):
    """State for the LangGraph agent"""
    logs: str
    context: Optional[str]
    diagnostics: Optional[List[str]]
    analysis: Optional[Dict[str, Any]]
    result: Optional[LogAnalysisResult]
    error: Optional[str]


class LogAnalysisAgent:
    """Claude-based agent for analyzing backend/server logs."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("Claude API key not provided. Set CLAUDE_API_KEY or pass it explicitly.")

        self.config = ClaudeConfig.from_env()

        llm_kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens_to_sample": self.config.max_tokens_to_sample,
            "api_key": self.api_key,
        }
        if self.config.top_p is not None:
            llm_kwargs["top_p"] = self.config.top_p

        self.llm = ChatAnthropic(**llm_kwargs)

        self.prompt_template = PromptTemplate(
            input_variables=["logs", "context", "diagnostics"],
            template="""You are an expert backend reliability engineer. Study the logs and respond with JSON.

ERROR LOGS (sanitized):
{logs}

ENVIRONMENT CONTEXT:
{context}

DIAGNOSTIC NOTES:
{diagnostics}

Return valid JSON using:
{{
    "root_cause": "Primary failure reason",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "recommendations": ["short action steps"],
    "affected_components": ["component"],
    "detailed_analysis": "Concise explanation"
}}

Highlight causal chains and differentiators unique to the provided logs only.
"""
        )

        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        graph = StateGraph(AgentState)
        graph.add_node("analyze", self._analyze_node)
        graph.add_node("format", self._format_node)
        graph.set_entry_point("analyze")
        graph.add_edge("analyze", "format")
        graph.add_edge("format", END)
        return graph.compile()

    @staticmethod
    def _sanitize_logs(raw_logs: str, max_chars: int = 4000) -> str:
        minimized = raw_logs.strip()
        if len(minimized) <= max_chars:
            return minimized
        return minimized[-max_chars:]

    @staticmethod
    def _format_diagnostics(diagnostics: Optional[List[str]]) -> str:
        if not diagnostics:
            return "No extra diagnostic notes provided."
        return "\n".join(f"- {note}" for note in diagnostics)

    @staticmethod
    def _coerce_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in content)
        return str(content)

    @staticmethod
    def _parse_response_payload(payload: str) -> Dict[str, Any]:
        try:
            json_start = payload.find('{')
            json_end = payload.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(payload[json_start:json_end])
        except json.JSONDecodeError:
            pass
        return {
            "root_cause": "See detailed analysis",
            "severity": "UNKNOWN",
            "recommendations": [],
            "affected_components": [],
            "detailed_analysis": payload.strip()
        }

    @staticmethod
    def _enrich_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
        affected = data.get("affected_components", [])
        if isinstance(affected, str):
            data["affected_components"] = [comp.strip() for comp in affected.split(',') if comp.strip()]
        return data

    def _analyze_node(self, state: AgentState) -> AgentState:
        try:
            sanitized_logs = self._sanitize_logs(state.get("logs", ""))
            prompt = self.prompt_template.format(
                logs=sanitized_logs,
                context=state.get("context", "No additional context provided."),
                diagnostics=self._format_diagnostics(state.get("diagnostics"))
            )
            response = self.llm.invoke(prompt)
            content = self._coerce_content(response.content)
            analysis = self._enrich_analysis(self._parse_response_payload(content))
            state["analysis"] = analysis
        except Exception as exc:
            state["error"] = f"Claude analysis error: {exc}"
        return state

    def _format_node(self, state: AgentState) -> AgentState:
        if state.get("error"):
            return state
        analysis = state.get("analysis", {})
        result = LogAnalysisResult(
            root_cause=analysis.get('root_cause', 'Unable to determine'),
            severity=analysis.get('severity', 'UNKNOWN'),
            recommendations=analysis.get('recommendations', []),
            affected_components=analysis.get('affected_components', []),
            timestamp=datetime.now().isoformat(),
            raw_analysis=analysis.get('detailed_analysis', 'No detailed analysis available')
        )
        state["result"] = result
        return state

    def analyze_logs(
        self,
        logs: str,
        context: Optional[str] = None,
        diagnostics: Optional[List[str]] = None
    ) -> LogAnalysisResult:
        initial_state: AgentState = {
            "logs": logs,
            "context": context,
            "diagnostics": diagnostics,
            "analysis": None,
            "result": None,
            "error": None
        }
        final_state = self.workflow.invoke(initial_state)
        if final_state.get("error"):
            raise Exception(final_state["error"])
        return final_state["result"]

    def batch_analyze_logs(self, log_entries: List[Dict[str, Any]]) -> List[LogAnalysisResult]:
        results: List[LogAnalysisResult] = []
        for entry in log_entries:
            result = self.analyze_logs(
                logs=entry.get('logs', ''),
                context=entry.get('context'),
                diagnostics=entry.get('diagnostics')
            )
            results.append(result)
        return results

    def format_result(self, result: LogAnalysisResult) -> str:
        output = f"""
LOG ANALYSIS REPORT (Claude)
{'=' * 80}
Timestamp: {result.timestamp}
Model: {self.config.model} (temperature={self.config.temperature})
Severity: {result.severity}

ROOT CAUSE:
{result.root_cause}

AFFECTED COMPONENTS:
{', '.join(result.affected_components) if result.affected_components else 'Not specified'}

RECOMMENDATIONS:
"""
        for idx, rec in enumerate(result.recommendations, 1):
            output += f"{idx}. {rec}\n"
        output += f"\nDETAILED ANALYSIS:\n{result.raw_analysis}\n"
        output += "=" * 80
        return output


def main() -> None:
    sample_logs = """
    [2026-03-02 08:10:11] ERROR: Payment service timeout after 30s
    [2026-03-02 08:10:12] WARN: Circuit breaker tripped for payment-gateway
    [2026-03-02 08:10:13] ERROR: Retry attempt failed with status 504
    [2026-03-02 08:10:14] INFO: Degraded mode enabled for checkout pipeline
    """

    diagnostics = [
        "Gateway requests routed through regional proxy eu-central",
        "Spike in latency observed after deployment build #582"
    ]

    try:
        agent = LogAnalysisAgent()
        result = agent.analyze_logs(
            logs=sample_logs,
            context="Production checkout cluster running on Kubernetes",
            diagnostics=diagnostics
        )
        print(agent.format_result(result))
    except ValueError as err:
        print(f"Configuration Error: {err}")
        print("\nSet CLAUDE_API_KEY before running the agent.")
    except Exception as err:
        print(f"Error: {err}")


if __name__ == "__main__":
    main()
