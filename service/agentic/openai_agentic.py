"""
Agentic AI Service for Server Log Analysis
This service uses LangGraph and LangChain with OpenAI to analyze server logs and identify root causes of errors.
"""

import os
import json
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
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
class OpenAIConfig:
    """Runtime configuration for the OpenAI-powered agent"""
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: Optional[int] = None

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        model = os.getenv("OPENAI_MODEL_NAME", cls.model)
        try:
            temperature = float(os.getenv("OPENAI_TEMPERATURE", cls.temperature))
        except ValueError:
            temperature = cls.temperature

        max_tokens_env = os.getenv("OPENAI_MAX_TOKENS")
        max_tokens: Optional[int] = None
        if max_tokens_env:
            try:
                max_tokens = int(max_tokens_env)
            except ValueError:
                max_tokens = None

        return cls(model=model, temperature=temperature, max_tokens=max_tokens)


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    logs: str
    context: Optional[str]
    hints: Optional[List[str]]
    analysis: Optional[Dict[str, Any]]
    result: Optional[LogAnalysisResult]
    error: Optional[str]


class LogAnalysisAgent:
    """
    Agentic AI for analyzing server and backend logs to identify root causes of issues.
    Uses LangGraph and LangChain with OpenAI for intelligent analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Log Analysis Agent
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env variable
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass it to constructor.")
        
        self.config = OpenAIConfig.from_env()

        llm_kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "api_key": self.api_key,
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens is not None:
            llm_kwargs["max_tokens"] = self.config.max_tokens

        # Initialize LangChain LLM
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # Initialize prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["logs", "context", "hints"],
            template="""You are an expert backend engineer specializing in log analysis and debugging.
Analyze the following server/backend error logs and provide a comprehensive analysis.

ERROR LOGS:
{logs}

ADDITIONAL CONTEXT:
{context}

CONTEXTUAL HINTS:
{hints}

Please provide your analysis in the following JSON format:
{{
    "root_cause": "Primary reason for the error",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "recommendations": ["step 1", "step 2", "..."],
    "affected_components": ["component1", "component2", "..."],
    "detailed_analysis": "Comprehensive explanation of the issue"
}}

Focus on:
1. Identifying the root cause of the error
2. Understanding the chain of events that led to the failure
3. Providing actionable recommendations to fix the issue
4. Identifying affected system components
5. Assessing the severity and impact

Return only valid JSON."""
        )
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()

    @staticmethod
    def _format_hints(hints: Optional[List[str]]) -> str:
        if not hints:
            return "No diagnostic hints provided"
        return "\n".join(f"- {hint}" for hint in hints)

    @staticmethod
    def _coerce_message_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(content)

    def _parse_analysis_response(self, analysis_text: str) -> Dict[str, Any]:
        try:
            json_start = analysis_text.find('{')
            json_end = analysis_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = analysis_text[json_start:json_end]
                parsed = json.loads(json_str)
            else:
                parsed = {
                    'root_cause': 'See detailed analysis',
                    'severity': 'UNKNOWN',
                    'recommendations': [],
                    'affected_components': [],
                    'detailed_analysis': analysis_text
                }
        except json.JSONDecodeError:
            parsed = {
                'root_cause': 'Analysis completed (see raw_analysis for details)',
                'severity': 'UNKNOWN',
                'recommendations': [],
                'affected_components': [],
                'detailed_analysis': analysis_text
            }

        return parsed
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow for log analysis
        
        Returns:
            Compiled StateGraph workflow
        """
        # Create the graph
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("analyze", self._analyze_node)
        graph.add_node("format", self._format_node)
        
        # Define edges
        graph.set_entry_point("analyze")
        graph.add_edge("analyze", "format")
        graph.add_edge("format", END)
        
        # Compile and return
        return graph.compile()
    
    def _analyze_node(self, state: AgentState) -> AgentState:
        """
        Node to analyze logs using LLM
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with analysis
        """
        try:
            # Format prompt with contextual hints
            prompt = self.prompt_template.format(
                logs=state["logs"],
                context=state.get("context", "No additional context provided"),
                hints=self._format_hints(state.get("hints"))
            )

            # Generate and parse analysis
            response = self.llm.invoke(prompt)
            analysis_text = self._coerce_message_content(response.content)
            analysis_data = self._parse_analysis_response(analysis_text)
            
            state["analysis"] = analysis_data
            
        except Exception as e:
            state["error"] = f"Error during analysis: {str(e)}"
        
        return state
    
    def _format_node(self, state: AgentState) -> AgentState:
        """
        Node to format analysis results
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with formatted result
        """
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
    
    def analyze_logs(self, logs: str, context: Optional[str] = None, hints: Optional[List[str]] = None) -> LogAnalysisResult:
        """
        Analyze server logs to identify root causes and provide recommendations
        
        Args:
            logs: The error logs to analyze (string format)
            context: Optional additional context about the system/environment
            hints: Optional list of targeted diagnostic hints
            
        Returns:
            LogAnalysisResult object containing structured analysis
        """
        # Initialize state
        initial_state: AgentState = {
            "logs": logs,
            "context": context,
            "hints": hints,
            "analysis": None,
            "result": None,
            "error": None
        }
        
        # Run the workflow
        final_state = self.workflow.invoke(initial_state)
        
        # Check for errors
        if final_state.get("error"):
            raise Exception(final_state["error"])
        
        return final_state["result"]
    
    def batch_analyze_logs(self, log_entries: List[Dict[str, Any]]) -> List[LogAnalysisResult]:
        """
        Analyze multiple log entries in batch
        
        Args:
            log_entries: List of dictionaries with 'logs' and optional 'context'/'hints' keys
            
        Returns:
            List of LogAnalysisResult objects
        """
        results = []
        for entry in log_entries:
            logs = entry.get('logs', '')
            context = entry.get('context')
            hints = entry.get('hints')
            result = self.analyze_logs(logs, context, hints)
            results.append(result)
        
        return results

    def summarize_batch_results(self, results: List[LogAnalysisResult]) -> str:
        if not results:
            return "No analyses were executed."

        severity_counts: Dict[str, int] = {}
        component_tally: Dict[str, int] = {}
        for result in results:
            severity_counts[result.severity] = severity_counts.get(result.severity, 0) + 1
            for component in result.affected_components:
                component_tally[component] = component_tally.get(component, 0) + 1

        severities = ", ".join(f"{level}: {count}" for level, count in severity_counts.items()) or "None"
        components = ", ".join(
            f"{component} ({count})" for component, count in sorted(component_tally.items(), key=lambda item: item[1], reverse=True)
        ) or "None"

        summary = [
            f"Total analyses: {len(results)}",
            f"Severity distribution: {severities}",
            f"Frequently affected components: {components}"
        ]

        return "\n".join(summary)
    
    def format_result(self, result: LogAnalysisResult) -> str:
        """
        Format analysis result for human-readable output
        
        Args:
            result: LogAnalysisResult object
            
        Returns:
            Formatted string
        """
        output = f"""
    LOG ANALYSIS REPORT
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
        for i, rec in enumerate(result.recommendations, 1):
            output += f"{i}. {rec}\n"
        
        output += f"\nDETAILED ANALYSIS:\n{result.raw_analysis}\n"
        output += "=" * 80
        
        return output


def main():
    """
    Example usage of the Log Analysis Agent
    """
    # Example error logs
    sample_logs = """
    [2026-03-01 10:23:45] ERROR: Database connection failed
    [2026-03-01 10:23:45] ERROR: psycopg2.OperationalError: could not connect to server: Connection refused
    [2026-03-01 10:23:45] ERROR: Is the server running on host "localhost" (127.0.0.1) and accepting TCP/IP connections on port 5432?
    [2026-03-01 10:23:46] ERROR: API endpoint /users failed with status 500
    [2026-03-01 10:23:46] ERROR: Traceback: Internal Server Error - Database unavailable
    """
    
    try:
        # Initialize agent
        agent = LogAnalysisAgent()
        
        # Analyze logs
        print("Analyzing server logs...")
        result = agent.analyze_logs(
            logs=sample_logs,
            context="PostgreSQL database running in Docker container on production server",
            hints=[
                "Inspect Docker network bridge for dropped packets",
                "Validate connection pooling configuration"
            ]
        )
        
        # Display results
        print(agent.format_result(result))
        print("\nBatch summary preview:")
        print(agent.summarize_batch_results([result]))
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nPlease set your OPENAI_API_KEY environment variable:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
