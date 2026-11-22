"""agentic-gate: a workflow gate that an agent cannot approve.

Upstream's built-in `gate` step takes its verdict from a workflow input, so anything that can run
`specify workflow resume --input verdict=approve` can pass it. This step has no verdict input. It
asks the kit whether a valid approval exists: a mirrored decision record whose evidence hash matches
the files, backed by a review that passes CK-APPROVER and CK-GATE-MIRROR. Until then it returns PAUSED.

Config:
    gate: G1..G7                       (required)
    spec: "<folder under specs/>"      (optional; defaults to the most recently changed spec)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression

LAUNCHER = ".specify/extensions/agentic/scripts/agentic.py"
GATES = ("G1", "G2", "G3", "G4", "G5", "G6", "G7")
PROFILE_GATES = {"lite": ("G1", "G3", "G5")}
BLOCKING = ("CK-GATE-RECORD", "CK-APPROVER", "CK-GATE-MIRROR")


class AgenticGateStep(StepBase):
    type_key = "agentic-gate"

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = []
        if config.get("gate") not in GATES:
            errors.append(f"agentic-gate: 'gate' must be one of {', '.join(GATES)}")
        for key in ("verdict_input", "options", "on_reject", "default"):
            if key in config:
                errors.append(f"agentic-gate: '{key}' is not supported; approval comes only from the enforcement channel")
        return errors

    @staticmethod
    def _kit(root: Path, *args: str) -> tuple[int, Any]:
        p = subprocess.run([sys.executable, str(root / LAUNCHER), "--root", str(root), *args],
                           capture_output=True, text=True, timeout=300)
        try:
            return p.returncode, json.loads(p.stdout)
        except json.JSONDecodeError:
            return p.returncode, {"error": (p.stderr or p.stdout).strip()[-400:]}

    @staticmethod
    def _latest_spec(root: Path) -> str | None:
        specs = [p.parent for p in (root / "specs").glob("*/spec.md")] if (root / "specs").is_dir() else []
        return max(specs, key=lambda d: d.stat().st_mtime).name if specs else None

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        problems = self.validate(config)
        if problems:
            return StepResult(status=StepStatus.FAILED, error="; ".join(problems))
        root = Path(context.project_root or ".").resolve()
        if not (root / LAUNCHER).is_file():
            return StepResult(status=StepStatus.FAILED, error="the agentic extension is not installed in this project")
        gate = config["gate"]
        spec = config.get("spec")
        if isinstance(spec, str) and "{{" in spec:
            spec = evaluate_expression(spec, context)
        spec = str(spec).strip() if spec else self._latest_spec(root)
        if not spec:
            return StepResult(status=StepStatus.FAILED, error="agentic-gate: no spec found under specs/")

        profile = "standard"
        kit = root / ".specify" / "agentic" / "kit.yml"
        if kit.is_file():
            for line in kit.read_text(encoding="utf-8").splitlines():
                if line.startswith("profile:"):
                    profile = line.split(":", 1)[1].split("#")[0].strip()
        if gate not in PROFILE_GATES.get(profile, GATES):
            return StepResult(output={"gate": gate, "spec": spec, "choice": "not-required",
                                      "message": f"{gate} is not required by the {profile} profile"})

        code, info = self._kit(root, "gate", "--spec", spec, "--gate", gate, "--json")
        if code == 0 and info.get("required") is False:  # folded into another gate by the lane the kit computed
            return StepResult(output={"gate": gate, "spec": spec, "choice": "not-required", "message": info.get("status", "")})
        if code != 0 or "hash" not in info:
            return StepResult(status=StepStatus.FAILED, error=f"agentic-gate: {info.get('error', 'could not read the gate')}")
        output = {"gate": gate, "spec": spec, "hash": info["hash"], "evidence": info["evidence"],
                  "required_roles": info["required_roles"], "paste": info["paste"], "choice": None}
        status = str(info.get("status", ""))
        if status.startswith("reject") and "DIFFERENT" not in status:
            output["choice"] = "reject"
            return StepResult(status=StepStatus.FAILED, output=output,
                              error=f"gate {gate} for {spec} was rejected by a reviewer")
        if info.get("approved"):
            code, report = self._kit(root, "check", *BLOCKING, "--json")
            if code == 0:
                output["choice"] = "approve"
                return StepResult(output=output)
            failing = [f for r in report.get("results", []) for f in r.get("findings", [])] or \
                      [r.get("not_run") for r in report.get("results", []) if r.get("not_run")] or [report.get("error", "")]
            output["message"] = "a decision is recorded but it is not valid: " + "; ".join(str(x) for x in failing[:3])
            return StepResult(status=StepStatus.PAUSED, output=output)
        output["message"] = (f"Gate {gate} for {spec} needs a human approval from: {', '.join(info['required_roles'])}. "
                             f"The reviewer submits an approving review containing: {info['paste']}")
        return StepResult(status=StepStatus.PAUSED, output=output)

    def can_resume(self, state: dict[str, Any]) -> bool:
        return True
