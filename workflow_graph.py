# # workflow_graph.py
# from typing import TypedDict, List
# import os

# from langgraph.graph import StateGraph, END
# from src.utils.logger import log_experiment, ActionType


# class WorkflowState(TypedDict):
#     target_dir: str
#     files: List[str]
#     problems: List[str]
#     fixed: List[str]
#     test_passed: bool


# def read_files(state: WorkflowState):
#     target_dir = state["target_dir"]
#     files = os.listdir(target_dir) if os.path.exists(target_dir) else []

#     log_experiment(
#         agent_name="ReadFiles",
#         model_used="no-llm",
#         action=ActionType.ANALYSIS,
#         details={
#             "input_prompt": f"Scan directory {target_dir}",
#             "output_response": f"Found {len(files)} files"
#         },
#         status="SUCCESS"
#     )

#     return {"files": files}


# def auditor(state: WorkflowState):
#     files = state.get("files", [])
#     problems = [f for f in files if f.endswith(".py")]

#     log_experiment(
#         agent_name="Auditor",
#         model_used="no-llm",
#         action=ActionType.ANALYSIS,
#         details={
#             "input_prompt": "Analyze files",
#             "output_response": f"Found {len(problems)} problematic files"
#         },
#         status="SUCCESS"
#     )

#     return {"problems": problems}


# def debugger(state: WorkflowState):
#     problems = state.get("problems", [])
#     fixed = [f"debug-{p}" for p in problems]

#     log_experiment(
#         agent_name="Debugger",
#         model_used="no-llm",
#         action=ActionType.FIX,
#         details={
#             "input_prompt": f"Fix files: {problems}",
#             "output_response": f"Fixed files: {fixed}"
#         },
#         status="SUCCESS"
#     )

#     return {"fixed": fixed}


# def tester(state: WorkflowState):
#     test_passed = True

#     log_experiment(
#         agent_name="Tester",
#         model_used="no-llm",
#         action=ActionType.DEBUG,
#         details={
#             "input_prompt": "Run tests",
#             "output_response": "All tests passed"
#         },
#         status="SUCCESS"
#     )

#     return {"test_passed": test_passed}


# def documenter(state: WorkflowState):
#     log_experiment(
#         agent_name="Documenter",
#         model_used="no-llm",
#         action=ActionType.GENERATION,
#         details={
#             "input_prompt": "Generate documentation",
#             "output_response": "Documentation generated"
#         },
#         status="SUCCESS"
#     )

#     return {}


# # -------- BUILD GRAPH --------

# builder = StateGraph(WorkflowState)

# builder.add_node("read_files", read_files)
# builder.add_node("auditor", auditor)
# builder.add_node("debugger", debugger)
# builder.add_node("tester", tester)
# builder.add_node("documenter", documenter)

# builder.set_entry_point("read_files")

# builder.add_edge("read_files", "auditor")

# builder.add_conditional_edges(
#     "auditor",
#     lambda state: "debugger" if state["problems"] else "documenter",
#     {
#         "debugger": "debugger",
#         "documenter": "documenter",
#     },
# )

# builder.add_edge("debugger", "tester")

# builder.add_conditional_edges(
#     "tester",
#     lambda state: "documenter" if state["test_passed"] else "debugger",
#     {
#         "documenter": "documenter",
#         "debugger": "debugger",
#     },
# )

# builder.add_edge("documenter", END)

# workflow = builder.compile()

# workflow_graph.py
from typing import TypedDict, List
import os
from dotenv import load_dotenv
from graphviz import Source

from langgraph.graph import StateGraph, END
from src.utils.logger import log_experiment, ActionType

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY and not os.getenv("USE_MOCK_LLM"):
    raise RuntimeError("GOOGLE_API_KEY not found in .env file")

# ---------------------------
# MOCK / REAL LLM toggle
# ---------------------------
USE_MOCK_LLM = True # Set False to use real Gemini API

# ---------------------------
# Import Gemini via LangChain or use Mock
# ---------------------------
if USE_MOCK_LLM:
    class MockLLM:
        def invoke(self, prompt: str):
            # Judge node should exit the loop
            if "judge" in prompt.lower() or "{files}" in prompt:
                class Resp:
                    content = "YES"
                return Resp()
            # Otherwise, return mock content
            return type("Resp", (), {"content": f"[MOCK RESPONSE] {prompt[:50]}..."})

    llm = MockLLM()
else:
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )

# ---------------------------
# Workflow state
# ---------------------------
class WorkflowState(TypedDict):
    target_dir: str
    files: List[str]
    problems: List[str]
    fixed: List[str]
    test_passed: bool

# ---------------------------
# Helper: load prompt from file
# ---------------------------
def load_prompt(filename: str) -> str:
    prompt_path = os.path.join("prompts", filename)  # relative to root
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

# ---------------------------
# Nodes
# ---------------------------
def read_files(state: WorkflowState):
    target_dir = state["target_dir"]
    files = os.listdir(target_dir) if os.path.exists(target_dir) else []

    log_experiment(
        agent_name="ReadFiles",
        model_used="no-llm",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": f"Scan directory {target_dir}",
            "output_response": f"Found {len(files)} files"
        },
        status="SUCCESS"
    )
    return {"files": files}

def auditor(state: WorkflowState):
    files = state.get("files", [])
    problems = []

    auditor_prompt_template = load_prompt("auditor_prompt.txt")

    for f in files:
        if f.endswith(".py"):
            filepath = os.path.join(state["target_dir"], f)
            with open(filepath, "r", encoding="utf-8") as file:
                code = file.read()

            prompt = auditor_prompt_template.format(code=code)
            response = llm.invoke(prompt)
            response_text = getattr(response, "content", str(response))
            problems.append(f"Issues in {f}:\n{response_text}")

            log_experiment(
                agent_name="Auditor",
                model_used="gemini-2.5-flash" if not USE_MOCK_LLM else "mock-llm",
                action=ActionType.ANALYSIS,
                details={
                    "file_analyzed": f,
                    "input_prompt": prompt,
                    "output_response": response_text
                },
                status="SUCCESS"
            )

    return {"problems": problems}

def fixer(state: WorkflowState):
    problems = state.get("problems", [])
    fixed = []

    if not problems:
        return {"fixed": fixed}

    fixer_prompt_template = load_prompt("fixer_prompt.txt")

    for problem in problems:
        prompt = fixer_prompt_template.format(issue=problem)
        response = llm.invoke(prompt)
        fixed_code = getattr(response, "content", f"debug-{problem}")
        fixed.append(fixed_code)

        log_experiment(
            agent_name="Fixer",
            model_used="gemini-2.5-flash" if not USE_MOCK_LLM else "mock-llm",
            action=ActionType.FIX,
            details={
                "problem_fixed": problem,
                "input_prompt": prompt,
                "output_response": fixed_code
            },
            status="SUCCESS"
        )

    return {"fixed": fixed}

def judge(state: WorkflowState):
    fixed_files = state.get("fixed", [])
    if not fixed_files:
        return {"test_passed": True}  # nothing to test

    judge_prompt_template = load_prompt("judge_prompt.txt")
    prompt = judge_prompt_template.replace("{files}", "\n".join(fixed_files))
    response = llm.invoke(prompt)
    response_text = getattr(response, "content", str(response))
    test_passed = "yes" in response_text.lower()

    log_experiment(
        agent_name="Judge",
        model_used="gemini-2.5-flash" if not USE_MOCK_LLM else "mock-llm",
        action=ActionType.DEBUG,
        details={
            "input_prompt": prompt,
            "output_response": response_text
        },
        status="SUCCESS"
    )

    return {"test_passed": test_passed}

def documenter(state: WorkflowState):
    files = state.get("files", [])
    for f in files:
        prompt = f"Generate professional documentation for {f}"
        response = llm.invoke(prompt)
        doc_text = getattr(response, "content", "Documentation generated")

        log_experiment(
            agent_name="Documenter",
            model_used="gemini-2.5-flash" if not USE_MOCK_LLM else "mock-llm",
            action=ActionType.GENERATION,
            details={
                "file_documented": f,
                "input_prompt": prompt,
                "output_response": doc_text
            },
            status="SUCCESS"
        )
    return {}

# ---------------------------
# Build workflow graph
# ---------------------------
builder = StateGraph(WorkflowState)

builder.add_node("read_files", read_files)
builder.add_node("auditor", auditor)
builder.add_node("fixer", fixer)
builder.add_node("judge", judge)
builder.add_node("documenter", documenter)

builder.set_entry_point("read_files")

builder.add_edge("read_files", "auditor")
builder.add_conditional_edges(
    "auditor",
    lambda state: "fixer" if state["problems"] else "documenter",
    {"fixer": "fixer", "documenter": "documenter"}
)
builder.add_edge("fixer", "judge")
builder.add_conditional_edges(
    "judge",
    lambda state: "documenter" if state["test_passed"] else "fixer",
    {"documenter": "documenter", "fixer": "fixer"}
)
builder.add_edge("documenter", END)

workflow = builder.compile()

from graphviz import Digraph

def export_workflow_graph(filename="workflow_graph"):
    dot = Digraph(comment="Workflow Graph")

    # Nodes you know exist
    nodes = ["read_files", "auditor", "fixer", "judge", "documenter", "END"]
    for n in nodes:
        dot.node(n, n)

    # Add edges exactly as you defined in your workflow
    dot.edge("read_files", "auditor")
    dot.edge("auditor", "fixer", label="if problems")
    dot.edge("auditor", "documenter", label="if no problems")
    dot.edge("fixer", "judge")
    dot.edge("judge", "documenter", label="if test passed")
    dot.edge("judge", "fixer", label="if test failed")
    dot.edge("documenter", "END")

    # Render PNG and PDF
    dot.render(filename, format="png", cleanup=True)
    dot.render(filename, format="pdf", cleanup=True)
    print(f"✅ Workflow graph exported as {filename}.png & {filename}.pdf")

# Call the function
export_workflow_graph()
