"""
Agentic AI Service for Server Log Analysis
This service uses Google Gemini API to analyze server logs and identify root causes of errors.
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai
from dataclasses import dataclass


@dataclass
class LogAnalysisResult:
    """Structured result from log analysis"""
    root_cause: str
    severity: str
    recommendations: List[str]
    affected_components: List[str]
    timestamp: str
    raw_analysis: str


class LogAnalysisAgent:
    """
    Agentic AI for analyzing server and backend logs to identify root causes of issues.
    Uses Google Gemini API for intelligent analysis.
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
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def _create_analysis_prompt(self, logs: str, context: Optional[str] = None) -> str:
        """
        Create a structured prompt for log analysis
        
        Args:
            logs: The error logs to analyze
            context: Optional additional context about the system
            
        Returns:
            Formatted prompt string
        """
        base_prompt = f"""You are an expert backend engineer specializing in log analysis and debugging.
Analyze the following server/backend error logs and provide a comprehensive analysis.

ERROR LOGS:
{logs}
"""
        
        if context:
            base_prompt += f"\nADDITIONAL CONTEXT:\n{context}\n"
        
        base_prompt += """
Please provide your analysis in the following JSON format:
{
    "root_cause": "Primary reason for the error",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "recommendations": ["step 1", "step 2", "..."],
    "affected_components": ["component1", "component2", "..."],
    "detailed_analysis": "Comprehensive explanation of the issue"
}

Focus on:
1. Identifying the root cause of the error
2. Understanding the chain of events that led to the failure
3. Providing actionable recommendations to fix the issue
4. Identifying affected system components
5. Assessing the severity and impact
"""
        return base_prompt
    
    def analyze_logs(self, logs: str, context: Optional[str] = None) -> LogAnalysisResult:
        """
        Analyze server logs to identify root causes and provide recommendations
        
        Args:
            logs: The error logs to analyze (string format)
            context: Optional additional context about the system/environment
            
        Returns:
            LogAnalysisResult object containing structured analysis
        """
        try:
            prompt = self._create_analysis_prompt(logs, context)
            
            # Generate analysis using Gemini
            response = self.model.generate_content(prompt)
            analysis_text = response.text
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (it might be wrapped in markdown code blocks)
                json_start = analysis_text.find('{')
                json_end = analysis_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = analysis_text[json_start:json_end]
                    analysis_data = json.loads(json_str)
                else:
                    # If no JSON found, create structured response from text
                    analysis_data = self._parse_unstructured_response(analysis_text)
                
                # Create result object
                result = LogAnalysisResult(
                    root_cause=analysis_data.get('root_cause', 'Unable to determine'),
                    severity=analysis_data.get('severity', 'UNKNOWN'),
                    recommendations=analysis_data.get('recommendations', []),
                    affected_components=analysis_data.get('affected_components', []),
                    timestamp=datetime.now().isoformat(),
                    raw_analysis=analysis_data.get('detailed_analysis', analysis_text)
                )
                
                return result
                
            except json.JSONDecodeError:
                # Fallback: return raw analysis
                return LogAnalysisResult(
                    root_cause="Analysis completed (see raw_analysis for details)",
                    severity="UNKNOWN",
                    recommendations=[],
                    affected_components=[],
                    timestamp=datetime.now().isoformat(),
                    raw_analysis=analysis_text
                )
                
        except Exception as e:
            raise Exception(f"Error during log analysis: {str(e)}")
    
    def _parse_unstructured_response(self, text: str) -> Dict[str, Any]:
        """
        Parse unstructured text response into structured format
        
        Args:
            text: Unstructured text response
            
        Returns:
            Dictionary with extracted information
        """
        return {
            'root_cause': 'See detailed analysis',
            'severity': 'UNKNOWN',
            'recommendations': [],
            'affected_components': [],
            'detailed_analysis': text
        }
    
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
