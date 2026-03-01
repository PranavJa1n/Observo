"""
Agentic AI Service for Server Log Analysis
This service uses LangGraph and LangChain with Google Gemini to analyze server logs and identify root causes of errors.
"""

import os
import json
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
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


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    logs: str
    context: Optional[str]
    analysis: Optional[Dict[str, Any]]
    result: Optional[LogAnalysisResult]
    error: Optional[str]


class LogAnalysisAgent:
    """
    Agentic AI for analyzing server and backend logs to identify root causes of issues.
    Uses LangGraph and LangChain with Google Gemini for intelligent analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Log Analysis Agent
        
        Args:
            api_key: Google Gemini API key. If not provided, reads from GEMINI_API_KEY env variable
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY environment variable or pass it to constructor.")
        
        # Initialize LangChain LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=self.api_key,
            temperature=0.3
        )
        
        # Initialize prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["logs", "context"],
            template="""You are an expert backend engineer specializing in log analysis and debugging.
Analyze the following server/backend error logs and provide a comprehensive analysis.

ERROR LOGS:
{logs}

ADDITIONAL CONTEXT:
{context}

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
            # Format prompt
            prompt = self.prompt_template.format(
                logs=state["logs"],
                context=state.get("context", "No additional context provided")
            )
            
            # Generate analysis
            response = self.llm.invoke(prompt)
            analysis_text = response.content
            
            # Parse JSON response
            try:
                json_start = analysis_text.find('{')
                json_end = analysis_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = analysis_text[json_start:json_end]
                    analysis_data = json.loads(json_str)
                else:
                    analysis_data = {
                        'root_cause': 'See detailed analysis',
                        'severity': 'UNKNOWN',
                        'recommendations': [],
                        'affected_components': [],
                        'detailed_analysis': analysis_text
                    }
            except json.JSONDecodeError:
                analysis_data = {
                    'root_cause': 'Analysis completed (see raw_analysis for details)',
                    'severity': 'UNKNOWN',
                    'recommendations': [],
                    'affected_components': [],
                    'detailed_analysis': analysis_text
                }
            
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
    
    def analyze_logs(self, logs: str, context: Optional[str] = None) -> LogAnalysisResult:
        """
        Analyze server logs to identify root causes and provide recommendations
        
        Args:
            logs: The error logs to analyze (string format)
            context: Optional additional context about the system/environment
            
        Returns:
            LogAnalysisResult object containing structured analysis
        """
        # Initialize state
        initial_state: AgentState = {
            "logs": logs,
            "context": context,
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
    
    def batch_analyze_logs(self, log_entries: List[Dict[str, str]]) -> List[LogAnalysisResult]:
        """
        Analyze multiple log entries in batch
        
        Args:
            log_entries: List of dictionaries with 'logs' and optional 'context' keys
            
        Returns:
            List of LogAnalysisResult objects
        """
        results = []
        for entry in log_entries:
            logs = entry.get('logs', '')
            context = entry.get('context')
            result = self.analyze_logs(logs, context)
            results.append(result)
        
        return results
    
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
            context="PostgreSQL database running in Docker container on production server"
        )
        
        # Display results
        print(agent.format_result(result))
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nPlease set your GEMINI_API_KEY environment variable:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
