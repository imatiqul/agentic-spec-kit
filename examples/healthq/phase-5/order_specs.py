"""Write the order between the reference specs into each spec's front matter (`depends_on.specs`).

    python examples/healthq/phase-5/order_specs.py [--check]

The kit requires two specs in flight that touch the same component to be ordered, directly (CK-CROSS-SPEC).
This script keeps one list, ORDER, and derives every pair from it: of two specs that share a component, the later
one in ORDER depends on the earlier. EXTRA holds dependencies that come from meaning and not from a shared component.
`--check` changes nothing and fails if a spec's front matter differs from what the list gives.
"""
import re
import sys
from pathlib import Path

import yaml

SPECS = Path(__file__).resolve().parents[1] / "project" / "specs"
#: Earlier lands first. 002 is last on purpose: in the reference it is analysis only, so nothing may wait for it.
ORDER = ["001-fail-closed-auth", "003-identity-from-token", "004-audit-identity", "007-audit-export-complete", "008-audit-append-only",
         "006-eval-production-path", "005-triage-validation", "015-audit-write-durable", "016-audit-record-content", "009-phi-protection",
         "013-migrations-production-engine", "010-bff-authorization", "011-frontend-route-guards", "012-no-fabricated-data", "014-pipeline-gates",
         "017-visible-failures", "018-reviewable-files", "019-skipped-tests", "020-repository-hygiene", "021-advisories-and-review",
         "022-cors-allowlist", "023-environment-values", "024-pinned-dev-containers", "025-event-contracts",
         "002-endpoint-authorization"]
EXTRA = {"005-triage-validation": ["006-eval-production-path"],            # the classifier is released on the evaluation's results
         "010-bff-authorization": ["001-fail-closed-auth", "003-identity-from-token"],
         "011-frontend-route-guards": ["001-fail-closed-auth"],
         "012-no-fabricated-data": ["006-eval-production-path"],             # real figures come from the evaluation
         "023-environment-values": ["001-fail-closed-auth"]}                  # a missing identity setting already stops a service


def front(text: str) -> dict:
    return yaml.safe_load(text.split("---")[1])


def wanted() -> dict[str, list[str]]:
    touches = {s: set(front((SPECS / s / "spec.md").read_text(encoding="utf-8"))["touches"]) for s in ORDER}
    out = {}
    for i, spec in enumerate(ORDER):
        deps = {earlier for earlier in ORDER[:i] if touches[earlier] & touches[spec]} | set(EXTRA.get(spec, []))
        out[spec] = sorted(deps)
    return out


def main(check: bool) -> int:
    on_disk = sorted(p.name for p in SPECS.iterdir() if (p / "spec.md").is_file())
    if on_disk != sorted(ORDER):
        print(f"ORDER and the specs on disk differ: {sorted(set(on_disk) ^ set(ORDER))}")
        return 1
    changed = []
    for spec, deps in wanted().items():
        path = SPECS / spec / "spec.md"
        text = path.read_text(encoding="utf-8")
        head, body = text.split("---", 2)[1], text.split("---", 2)[2]
        line = "  specs: [" + ", ".join(deps) + "]"
        new_head, n = re.subn(r"^  specs: \[.*\]$", line, head, count=1, flags=re.M)
        if n != 1:
            print(f"{spec}: no `specs:` line under depends_on")
            return 1
        if new_head != head:
            changed.append(spec)
            if not check:
                path.write_text("---" + new_head + "---" + body, encoding="utf-8", newline="\n")
    print(("would change: " if check else "changed: ") + (", ".join(changed) or "nothing"))
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv[1:]))
