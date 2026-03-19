"""
Agentic AI Service for Server Log Analysis using Perplexity models via LangChain.
"""

import os
import json
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
from dataclasses import dataclass

from langchain_perplexity import ChatPerplexity
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END


@dataclass
class LogAnalysisResult:
    """Structured result returned by the agent"""
    root_cause: str
    severity: str
    recommendations: List[str]
    affected_components: List[str]
    timestamp: str
    raw_analysis: str


@dataclass
class PerplexityConfig:
    """Runtime configuration sourced from environment variables."""
    model: str = "llama-3.1-sonar-large-128k-online"
    temperature: float = 0.1
    max_tokens: Optional[int] = 1024
    project_label: str = "observability-lab"

    @classmethod
    def from_env(cls) -> "PerplexityConfig":
        model = os.getenv("PERPLEXITY_MODEL_NAME", cls.model)
        temperature = cls.temperature
        try:
            temperature = float(os.getenv("PERPLEXITY_TEMPERATURE", temperature))
        except ValueError:
            pass

        max_tokens_val: Optional[int] = cls.max_tokens
        try:
            max_tokens_env = os.getenv("PERPLEXITY_MAX_TOKENS")
            if max_tokens_env is not None:
                max_tokens_val = int(max_tokens_env)
        except ValueError:
            max_tokens_val = cls.max_tokens

        project_label = os.getenv("PERPLEXITY_PROJECT_LABEL", cls.project_label)
        return cls(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens_val,
            project_label=project_label,
        )


class AgentState(TypedDict, total=False):
    logs: str
    context: Optional[str]
    focus_areas: Optional[List[str]]
    analysis: Optional[Dict[str, Any]]
    result: Optional[LogAnalysisResult]
    error: Optional[str]


class LogAnalysisAgent:
    """Perplexity-powered agent for diagnosing backend log issues."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError("Perplexity API key not provided. Set PERPLEXITY_API_KEY or pass it explicitly.")

        self.config = PerplexityConfig.from_env()

        llm_kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "api_key": self.api_key,
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens is not None:
            llm_kwargs["max_tokens"] = self.config.max_tokens

        self.llm = ChatPerplexity(**llm_kwargs)

        self.prompt_template = PromptTemplate(
            input_variables=["logs", "context", "focus", "project"],
            template="""You are a senior reliability engineer embedded on project {project}.
Evaluate the following structured logs and return JSON only.

LOG SAMPLE:
{logs}

ENVIRONMENT CONTEXT:
{context}

FOCUS AREAS:
{focus}

Your JSON response must match:
{{
    "root_cause": "single sentence summary",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "recommendations": ["short actionable steps"],
    "affected_components": ["service or subsystem"],
    "detailed_analysis": "succinct causal explanation"
}}

Call out any data gaps explicitly and never fabricate services that are not mentioned.
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
    def _trim_logs(logs: str, limit: int = 5000) -> str:
        condensed = logs.strip()
        if len(condensed) <= limit:
            return condensed
        return condensed[-limit:]

    @staticmethod
    def _format_focus(focus: Optional[List[str]]) -> str:
        if not focus:
            return "Stability, latency, data integrity"
        return "\n".join(f"- {item}" for item in focus)

    @staticmethod
    def _coerce_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(str(fragment) for fragment in content)
        return str(content)

    @staticmethod
    def _parse_json_payload(payload: str) -> Dict[str, Any]:
        try:
            start = payload.find('{')
            end = payload.rfind('}') + 1
            if start != -1 and end > start:
                parsed = json.loads(payload[start:end])
            else:
                parsed = {}
        except json.JSONDecodeError:
            parsed = {}

        if not parsed:
            parsed = {
                "root_cause": "See detailed analysis",
                "severity": "UNKNOWN",
                "recommendations": [],
                "affected_components": [],
                "detailed_analysis": payload.strip(),
            }
        return parsed

    def _analyze_node(self, state: AgentState) -> AgentState:
        try:
            prompt = self.prompt_template.format(
                logs=self._trim_logs(state.get("logs", "")),
                context=state.get("context", "No additional context provided."),
                focus=self._format_focus(state.get("focus_areas")),
                project=self.config.project_label,
            )
            response = self.llm.invoke(prompt)
            analysis_text = self._coerce_content(response.content)
            state["analysis"] = self._parse_json_payload(analysis_text)
        except Exception as exc:
            state["error"] = f"Perplexity analysis error: {exc}"
        return state

    def _format_node(self, state: AgentState) -> AgentState:
        if state.get("error"):
            return state
        analysis = state.get("analysis", {})
        state["result"] = LogAnalysisResult(
            root_cause=analysis.get('root_cause', 'Unable to determine'),
            severity=analysis.get('severity', 'UNKNOWN'),
            recommendations=analysis.get('recommendations', []),
            affected_components=analysis.get('affected_components', []),
            timestamp=datetime.now().isoformat(),
            raw_analysis=analysis.get('detailed_analysis', 'No detailed analysis available'),
        )
        return state

    def analyze_logs(
        self,
        logs: str,
        context: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
    ) -> LogAnalysisResult:
        initial_state: AgentState = {
            "logs": logs,
            "context": context,
            "focus_areas": focus_areas,
            "analysis": None,
            "result": None,
            "error": None,
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
                focus_areas=entry.get('focus_areas'),
            )
            results.append(result)
        return results

    def format_result(self, result: LogAnalysisResult) -> str:
        output = f"""
LOG ANALYSIS REPORT (Perplexity)
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

    def generate_incident_brief(self, results: List[LogAnalysisResult]) -> str:
        if not results:
            return "No analyses available for incident brief."
        worst = sorted(results, key=lambda r: r.severity, reverse=True)[0]
        body = [
            f"Highest severity detected: {worst.severity}",
            f"Root cause snapshot: {worst.root_cause}",
            f"Impact spread: {', '.join(worst.affected_components) or 'Not specified'}",
            f"Recommended first action: {worst.recommendations[0] if worst.recommendations else 'N/A'}",
        ]
        return "\n".join(body)


def main() -> None:
    sample_logs = """
    [2026-03-03 02:45:11] ERROR: Cache miss storm detected in region us-east-1
    [2026-03-03 02:45:12] WARN: Redis latency exceeded 250ms threshold
    [2026-03-03 02:45:13] ERROR: API /cart checkout returned 502 at shard-3
    [2026-03-03 02:45:14] INFO: Auto-healing attempting node recycle
    """

    try:
        agent = LogAnalysisAgent()
        result = agent.analyze_logs(
            logs=sample_logs,
            context="E-commerce checkout stack running on Kubernetes",
            focus_areas=["Redis cache", "Checkout API stability"],
        )
        print(agent.format_result(result))
        print("\nIncident brief preview:\n")
        print(agent.generate_incident_brief([result]))
    except ValueError as err:
        print(f"Configuration Error: {err}")
        print("\nSet PERPLEXITY_API_KEY before running the agent.")
    except Exception as err:
        print(f"Error: {err}")


if __name__ == "__main__":
    main()
