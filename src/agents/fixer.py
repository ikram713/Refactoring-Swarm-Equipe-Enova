# src/agents/fixer.py
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from src.utils.logger import log_experiment, ActionType

load_dotenv()

# Now os.getenv("GOOGLE_API_KEY") will return the key from .env
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

class FixerAgent:
    def __init__(self, prompt_path: str = "prompts/fixer_prompt.txt"):
        # Configure Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable is not set!")

        genai.configure(api_key=api_key)

        # Load model
        self.model_name = "models/gemini-2.5-flash"
        self.model = genai.GenerativeModel(self.model_name)

        # Load prompt
        prompt_file = Path(prompt_path)
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        self.prompt = prompt_file.read_text(encoding="utf-8")

    def run(self, file_path: Path, auditor_report: str, overwrite: bool = True) -> str:
        """
        Run the Fixer agent on a single file.
        Logs input_prompt and raw output_response.
        If overwrite=True, replaces the file content with the fixed code.
        Returns the raw output from the LLM (fixed code)
        """
        # Read original code
        code_text = file_path.read_text(encoding="utf-8")

        # Build input prompt
        input_prompt = f"""
{self.prompt}

AUDITOR REPORT:
{auditor_report}

FILE TO FIX:
FILE: {file_path}
```python
{code_text}
```"""

        # Call Gemini
        try:
            response = self.model.generate_content(input_prompt)
            output_response = response.text
            status = "SUCCESS"
        except Exception as e:
            output_response = str(e)
            status = "FAILURE"

        # Logging — mandatory for your assignment
        log_experiment(
            agent_name="FixerAgent",
            model_used=self.model_name,
            action=ActionType.FIX,
            details={
                "file": str(file_path),
                "auditor_report": auditor_report,
                "input_prompt": input_prompt,
                "output_response": output_response,
            },
            status=status
        )

        # Overwrite the original file if requested
        if overwrite and status == "SUCCESS":
            # Remove file wrapper if AI returns FILE: ... and ```python ... ```
            if "```" in output_response:
                fixed_code = output_response.split("```")[-2].strip()
            else:
                fixed_code = output_response.strip()

            file_path.write_text(fixed_code, encoding="utf-8")
            print(f"✔ File {file_path} updated with fixed code")

        return output_response
