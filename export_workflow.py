# export_workflow.py

from workflow_graph import workflow

# This generates a PNG image of the workflow graph
png_bytes = workflow.get_graph().draw_png()

with open("workflow.png", "wb") as f:
    f.write(png_bytes)

print("✅ Workflow exported to workflow.png")
