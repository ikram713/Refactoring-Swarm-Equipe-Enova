# src/agents/judge.py
import os
from pathlib import Path
from src.tools.test_runner import run_pytest
from src.utils.logger import log_experiment, ActionType


class JudgeAgent:
    """
    Judge Agent: Execute les tests unitaires et determine si le code est valide.
    Si tous les tests passent → SUCCESS
    Si un test echoue → FAILURE (la boucle doit recommencer)
    """

    def __init__(self, model_name="gemini-2.5-flash"):
        self.agent_name = "Judge_Agent"
        self.model_name = model_name

    def execute_tests(self, sandbox_dir: str) -> dict:
        """
        Execute tous les tests dans le dossier sandbox.
        
        Args:
            sandbox_dir: Chemin vers le dossier sandbox (ex: "./sandbox")
        
        Returns:
            dict: {
                "all_passed": True/False,
                "total_tests": int,
                "passed": int,
                "failed": int,
                "error_details": str
            }
        """
        # Convert to absolute path and resolve
        sandbox_path = Path(sandbox_dir).resolve()
        
        if not sandbox_path.exists():
            result = {
                "all_passed": False,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "error_details": f"Sandbox directory not found: {sandbox_dir} (resolved to {sandbox_path})"
            }
            self._log_results(str(sandbox_path), result, "FAILURE")
            return result

        # Look for test files in the sandbox
        test_files = list(sandbox_path.glob("test_*.py"))
        
        if not test_files:
            result = {
                "all_passed": False,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "error_details": f"No test files found in {sandbox_dir}. Expected files like test_*.py"
            }
            self._log_results(str(sandbox_path), result, "FAILURE")
            return result

        # Executer les tests avec pytest via test_runner
        try:
            # run_pytest expects a relative path from sandbox root
            # Pass just the directory name since test_runner uses _validate_path
            test_result = run_pytest("")  # Empty string means test all in sandbox
            
            # Adapter le format de run_pytest au format attendu
            # run_pytest retourne: {"success", "total", "passed", "failed", "errors", "summary"}
            all_passed = test_result.get("success", False)
            total_tests = test_result.get("total", 0)
            passed = test_result.get("passed", 0)
            failed = test_result.get("failed", 0)
            error_details = test_result.get("summary", "")
            
            result = {
                "all_passed": all_passed,
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "error_details": error_details
            }
            
            status = "SUCCESS" if all_passed else "FAILURE"
            self._log_results(sandbox_dir, result, status)
            
            return result
            
        except Exception as e:
            result = {
                "all_passed": False,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "error_details": f"Error executing tests: {str(e)}"
            }
            self._log_results(sandbox_dir, result, "FAILURE")
            return result

    def _log_results(self, sandbox_dir: str, result: dict, status: str):
        """Log les resultats dans experiment_data.json"""
        
        # Creer le prompt d'entree (ce qu'on demande au Judge)
        input_prompt = f"""Execute all unit tests in directory: {sandbox_dir}
        
Judge must verify if all tests pass.
If yes → Mission complete
If no → Loop must restart"""

        # Creer la reponse de sortie (ce que le Judge a trouve)
        output_response = f"""TEST EXECUTION RESULTS:
Total tests: {result['total_tests']}
Passed: {result['passed']}
Failed: {result['failed']}
All passed: {result['all_passed']}

MISSION_STATUS: {"SUCCESS" if result['all_passed'] else "FAILURE"}

Details:
{result['error_details'][:500]}"""  # Limiter a 500 chars

        # Logger l'action (OBLIGATOIRE pour la note)
        log_experiment(
            agent_name=self.agent_name,
            model_used=self.model_name,
            action=ActionType.DEBUG,  # Judge = DEBUG (verification des tests)
            details={
                "sandbox_directory": sandbox_dir,
                "input_prompt": input_prompt,  # OBLIGATOIRE
                "output_response": output_response,  # OBLIGATOIRE
                "total_tests": result['total_tests'],
                "tests_passed": result['passed'],
                "tests_failed": result['failed'],
                "all_passed": result['all_passed']
            },
            status=status
        )

    def print_summary(self, result: dict):
        """Affiche un resume des resultats dans la console"""
        print("\n" + "="*50)
        print("🔍 JUDGE AGENT - TEST RESULTS")
        print("="*50)
        print(f"Total tests: {result['total_tests']}")
        print(f"✅ Passed: {result['passed']}")
        print(f"❌ Failed: {result['failed']}")
        print("-"*50)
        
        if result['all_passed']:
            print("✅ ALL TESTS PASSED - MISSION COMPLETE!")
        else:
            print("❌ TESTS FAILED - LOOP MUST RESTART")
            print(f"\nError details:\n{result['error_details'][:300]}")
        
        print("="*50 + "\n")