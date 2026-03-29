"""Workflow entrypoints for the SVMP runtime."""

from svmp_core.workflows.workflow_a import run_workflow_a
from svmp_core.workflows.workflow_c import WorkflowCResult, run_workflow_c

__all__ = ["WorkflowCResult", "run_workflow_a", "run_workflow_c"]
