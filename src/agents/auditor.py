"""
Auditor Agent for The Refactoring Swarm
========================================
Analyzes Python code for bugs, bad practices, and quality issues.

This agent reads code, runs static analysis, and produces a
detailed refactoring plan using LLM assistance.

"""

import os
import google.generativeai as genai
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import toolsmith functions
from src.tools import (
    read_file,
    list_python_files,
    run_pylint,
    analyse_report,
    get_code_metrics
)

# Import logging
from src.utils.logger import log_experiment, ActionType


class AuditorAgent:
    """
    Auditor Agent: Analyzes code quality and generates refactoring plans.
    
    Responsibilities:
    - Read Python code from sandbox
    - Run static analysis (Pylint)
    - Send to LLM for deep analysis
    - Generate prioritized refactoring plan
    - Log all interactions
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the Auditor Agent.
        
        Args:
            model_name: Gemini model to use
        """
        self.model_name = model_name
        self.agent_name = "Auditor_Agent"
        
        # Load system prompt
        self.system_prompt = self._load_prompt()
        
        # Configure Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def _load_prompt(self) -> str:
        """
        Load the auditor system prompt from prompts/auditor_prompt.txt
        
        Returns:
            str: System prompt content
        """
        prompt_path = os.path.join("prompts", "auditor_prompt.txt")
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback prompt if file not found
            return """You are an expert Python code auditor.
Analyze the provided code and identify:
- Bugs or logical errors
- Bad coding practices
- Missing documentation
- Readability issues

Provide a numbered list of issues with clear explanations."""
    
    def analyze_file(self, file_path: str) -> Dict:
        """
        Analyze a single Python file.
        
        Args:
            file_path: Path to Python file (relative to sandbox)
        
        Returns:
            dict: Analysis results with structure:
                {
                    "file": str,
                    "pylint_score": float,
                    "pylint_issues": list,
                    "code_metrics": dict,
                    "llm_analysis": str,
                    "refactoring_plan": dict,
                    "status": str
                }
        """
        print(f"\n{'='*60}")
        print(f"🔍 AUDITOR AGENT: Analyzing {file_path}")
        print(f"{'='*60}")
        
        try:
            # Step 1: Read the code
            print(f"[1/5] Reading file...")
            code_content = read_file(file_path)
            
            # Step 2: Run Pylint analysis
            print(f"[2/5] Running Pylint analysis...")
            pylint_result = run_pylint(file_path)
            
            # Step 3: Get code metrics
            print(f"[3/5] Extracting code metrics...")
            metrics = get_code_metrics(file_path)
            
            # Step 4: Generate analysis report (using your tool)
            print(f"[4/5] Generating analysis report...")
            plan = analyse_report(file_path)
            
            # Step 5: Send to LLM for deep analysis
            print(f"[5/5] Analyzing with LLM...")
            llm_analysis, full_prompt = self._analyze_with_llm(
                code_content=code_content,
                file_name=file_path,
                pylint_score=pylint_result['score'],
                pylint_issues=pylint_result['issues'],
                priority_issues=plan['priority_issues']
            )
            
            # Prepare result
            result = {
                "file": file_path,
                "pylint_score": pylint_result['score'],
                "pylint_issues": pylint_result['issues'][:10],  # Top 10 issues
                "code_metrics": metrics,
                "llm_analysis": llm_analysis,
                "analysis_report": plan,
                "status": "SUCCESS"
            }
            
            # Log the interaction
            self._log_analysis(
                file_path=file_path,
                code_content=code_content,
                llm_analysis=llm_analysis,
                pylint_score=pylint_result['score'],
                total_issues=len(pylint_result['issues']),
                full_prompt=full_prompt
            )
            
            # Print summary
            self._print_summary(result)
            
            return result
            
        except Exception as e:
            error_result = {
                "file": file_path,
                "status": "ERROR",
                "error": str(e)
            }
            
            print(f" Error analyzing {file_path}: {str(e)}")
            import traceback
            print(f"Full traceback:\n{traceback.format_exc()}")
            
            # Log the error with required fields
            try:
                log_experiment(
                    agent_name=self.agent_name,
                    model_used=self.model_name,
                    action=ActionType.ANALYSIS,
                    details={
                        "file_analyzed": file_path,
                        "input_prompt": f"Error occurred before prompt generation for {file_path}",
                        "output_response": f"ERROR: {str(e)}",
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    },
                    status="ERROR"
                )
            except Exception as log_error:
                print(f" Could not log error: {log_error}")
            
            return error_result
    
    def _analyze_with_llm(
        self,
        code_content: str,
        file_name: str,
        pylint_score: float,
        pylint_issues: List[Dict],
        priority_issues: List[Dict]
    ) -> tuple[str, str]:
        """
        Send code to LLM for deep analysis.
        
        Args:
            code_content: The source code
            file_name: Name of the file
            pylint_score: Score from Pylint
            pylint_issues: List of Pylint issues
            priority_issues: Priority issues from analyse_report
        
        Returns:
            tuple: (LLM analysis, full prompt)
        """
        # Ensure pylint_issues is a list
        if not isinstance(pylint_issues, list):
            pylint_issues = []
        
        # Ensure priority_issues is a list
        if not isinstance(priority_issues, list):
            priority_issues = []
        
        # Prepare context for LLM
        pylint_summary = f"Pylint Score: {pylint_score}/10\n"
        pylint_summary += f"Total issues: {len(pylint_issues)}\n\n"
        
        if pylint_issues and len(pylint_issues) > 0:
            pylint_summary += "Top issues:\n"
            for i, issue in enumerate(pylint_issues[:5], 1):
                try:
                    pylint_summary += f"{i}. Line {issue.get('line', 'N/A')}: {issue.get('message', 'Unknown')}\n"
                except (AttributeError, TypeError) as e:
                    print(f"Warning: Issue formatting error: {e}")
                    continue
        
        # Build priority issues text
        priority_text = ""
        if priority_issues and len(priority_issues) > 0:
            priority_text = "Priority Issues:\n"
            for issue in priority_issues[:5]:
                try:
                    priority_text += f"- [{issue.get('priority', 'unknown')}] Line {issue.get('line', 'N/A')}: {issue.get('message', 'Unknown')}\n"
                except (AttributeError, TypeError) as e:
                    print(f"Warning: Priority issue formatting error: {e}")
                    continue
        
        # Build the full prompt
        full_prompt = f"""{self.system_prompt}

FILE: {file_name}

STATIC ANALYSIS RESULTS:
{pylint_summary}

{priority_text}

SOURCE CODE:
```python
{code_content}
```

Please analyze this code and provide your findings in the specified format.
"""
        
        # Call Gemini
        try:
            response = self.model.generate_content(full_prompt)
            llm_response = response.text if hasattr(response, 'text') else str(response)
            return llm_response, full_prompt
        except Exception as e:
            error_msg = f"LLM_ERROR: {str(e)}"
            print(f"LLM Error: {e}")
            return error_msg, full_prompt
    
    def _log_analysis(
        self,
        file_path: str,
        code_content: str,
        llm_analysis: str,
        pylint_score: float,
        total_issues: int,
        full_prompt: str = ""
    ):
        """
        Log the auditor's analysis for research purposes.
        
        Args:
            file_path: File being analyzed
            code_content: Source code
            llm_analysis: LLM's analysis
            pylint_score: Pylint quality score
            total_issues: Number of issues found
            full_prompt: The complete prompt sent to LLM
        """
        log_experiment(
            agent_name=self.agent_name,
            model_used=self.model_name,
            action=ActionType.ANALYSIS,
            details={
                "file_analyzed": file_path,
                "input_prompt": full_prompt,  # Full prompt (required)
                "output_response": llm_analysis,  # LLM response (required)
                "pylint_score": pylint_score,
                "issues_found": total_issues,
                "code_length": len(code_content)
            },
            status="SUCCESS"
        )
    
    def _print_summary(self, result: Dict):
        """
        Print a human-readable summary of the analysis.
        
        Args:
            result: Analysis result dictionary
        """
        print(f"\n ANALYSIS SUMMARY")
        print(f"{'─'*60}")
        print(f"File: {result['file']}")
        print(f"Pylint Score: {result['pylint_score']}/10")
        print(f"Issues Found: {len(result['pylint_issues'])}")
        print(f"Lines of Code: {result['code_metrics']['code_lines']}")
        print(f"Functions: {result['code_metrics']['functions']}")
        print(f"Classes: {result['code_metrics']['classes']}")
        print(f"\n LLM Analysis:")
        print(f"{result['llm_analysis']}...")
        print(f"{'─'*60}\n")
    
    def analyze_directory(self, directory: str = "") -> List[Dict]:
        """
        Analyze all Python files in a directory.
        
        Args:
            directory: Directory path (relative to sandbox)
        
        Returns:
            list: List of analysis results for each file
        """
        print(f"\n{'='*60}")
        print(f" AUDITOR AGENT: Analyzing directory")
        print(f"{'='*60}")
        
        # Get all Python files
        python_files = list_python_files(directory)
        
        # Filter out test files (Auditor doesn't analyze tests)
        source_files = [f for f in python_files if not f.startswith("test_")]
        
        print(f"Found {len(source_files)} source files to analyze")
        
        results = []
        for file_path in source_files:
            result = self.analyze_file(file_path)
            results.append(result)
        
        # Print overall summary
        self._print_directory_summary(results)
        
        return results
    
    def _print_directory_summary(self, results: List[Dict]):
        """
        Print summary for directory analysis.
        
        Args:
            results: List of analysis results
        """
        successful = [r for r in results if r['status'] == 'SUCCESS']
        failed = [r for r in results if r['status'] == 'ERROR']
        
        avg_score = sum(r['pylint_score'] for r in successful) / len(successful) if successful else 0
        total_issues = sum(len(r['pylint_issues']) for r in successful)
        
        print(f"\n{'='*60}")
        print(f"DIRECTORY ANALYSIS SUMMARY")
        print(f"{'='*60}")
        print(f"Total files analyzed: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print(f"Average Pylint Score: {avg_score:.2f}/10")
        print(f"Total Issues Found: {total_issues}")
        print(f"{'='*60}\n")


def auditor_agent(target_path: str) -> Dict:
    """
    Convenience function to run the Auditor Agent.
    
    This function can be called by the Orchestrator to analyze code.
    
    Args:
        target_path: Path to file or directory to analyze
    
    Returns:
        dict: Analysis results
    
    Example:
        >>> result = auditor_agent("messy_code.py")
        >>> print(result['pylint_score'])
        5.5
    """
    agent = AuditorAgent()
    
    # Check if it's a file or directory
    from src.tools import file_exists
    
    if file_exists(target_path):
        # Single file
        return agent.analyze_file(target_path)
    else:
        # Assume it's a directory
        results = agent.analyze_directory(target_path)
        return {
            "type": "directory",
            "path": target_path,
            "results": results,
            "summary": {
                "total_files": len(results),
                "avg_score": sum(r.get('pylint_score', 0) for r in results) / len(results) if results else 0
            }
        }


if __name__ == "__main__":
    """
    Self-test: Run the Auditor Agent on a sample file.
    """
    print("=" * 60)
    print("AUDITOR AGENT SELF-TEST")
    print("=" * 60)
    
    from src.tools import write_file, ensure_sandbox_exists
    
    # Ensure sandbox exists
    ensure_sandbox_exists()
    
    # Create a messy test file
    messy_code = '''
def foo(x,y):
    z=x+y
    return z

class myClass:
    def bar(self):
        pass

def unused_function():
    a=1
    b=2
    return a
        
   
'''
    
    print("\n[Setup] Creating test file...")
    write_file("auditor_test.py", messy_code)
    
    print("\n[Test] Running Auditor Agent...")
    
    try:
        # Run the agent
        result = auditor_agent("auditor_test.py")
        
        if result['status'] == 'SUCCESS':
            print("\n PASSED: Auditor Agent executed successfully")
            print(f"   Score: {result['pylint_score']}/10")
            print(f"   Issues: {len(result['pylint_issues'])}")
        else:
            print(f"\n FAILED: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\nFAILED: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Self-test completed!")
    print("=" * 60)