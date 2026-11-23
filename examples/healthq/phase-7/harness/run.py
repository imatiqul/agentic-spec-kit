#!/usr/bin/env python3
"""Compile and run the tests of spec 004-audit-identity without the solution's NuGet packages.

    python run.py --repo <healthcare clone>                 run the tests against the working copy
    python run.py --repo <healthcare clone> --at <ref>      run the tests as they are at a commit
    python run.py --repo <healthcare clone> --seed          make one defect at a time, in the middleware
                                                            or in how a service registers it, and say
                                                            whether the tests catch each
    python run.py --repo <healthcare clone> --seed --base <ref>
                                                            also put the nine services back in the
                                                            order they have at <ref>

The stand-in project is copied to a temporary directory and built there; the healthcare clone is
only read, except for a build output directory under tests/HealthQCopilot.Tests.Unit/bin/, which
the repository ignores and which is removed afterwards. Seeded defects are applied to a temporary
copy of the files, never to the clone.

Needs the .NET SDK the solution targets, and nothing from a package registry.
Exit status: 0 when every test passed (and, with --seed, every seeded defect was caught).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MIDDLEWARE = "src/HealthQCopilot.Infrastructure/Middleware/PhiAuditMiddleware.cs"

# What the stand-in project compiles or reads from the repository.
NEEDED = [
    "HealthQCopilot.sln",
    "Directory.Build.props",
    ".editorconfig",
    MIDDLEWARE,
    "src/HealthQCopilot.Infrastructure/Middleware/TenantContextMiddleware.cs",
    "src/HealthQCopilot.Infrastructure/Messaging/IEventHubAuditService.cs",
    "src/HealthQCopilot.Infrastructure/Messaging/AuditEvent.cs",
    "tests/HealthQCopilot.Tests.Unit/Infrastructure/PhiAuditMiddlewareTests.cs",
    "tests/HealthQCopilot.Tests.Unit/Infrastructure/PhiAuditPipelineTests.cs",
    "tests/HealthQCopilot.Tests.Unit/Architecture/RequestPipelineOrder.cs",
    "tests/HealthQCopilot.Tests.Unit/Architecture/RequestPipelineOrderTests.cs",
]

VOICE = "src/HealthQCopilot.Voice/Program.cs"
ORDER_TESTS = "tests/HealthQCopilot.Tests.Unit/Architecture/RequestPipelineOrderTests.cs"
HEADER = 'context.Request.Headers["X-User-Id"].FirstOrDefault()'
OLD_ORDER = """var app = builder.Build();
app.UseMiddleware<SecurityHeadersMiddleware>();
{audit}
app.UseAuthentication();
app.UseAuthorization();
app.Run();
"""

# Each seeded defect: what it is, then the edits that make it. An edit replaces text in a file, or writes a new file.
# D1 to D8 and O1 are the author's. The rest were added in the first rework round, from the reviewers' reports.
DEFECTS = [
    ("D1", "the user is taken from the oid claim, as before the change", [(MIDDLEWARE,
        """            var subject = identity.FindFirst("sub")?.Value
                ?? identity.FindFirst(ClaimTypes.NameIdentifier)?.Value;""",
        """            var subject = identity.FindFirst("oid")?.Value;""")]),
    ("D2", "the identity is read only before the rest of the pipeline runs", [
        (MIDDLEWARE, """        _logger.LogInformation(
            "PHI_ACCESS: User={UserId} Method={Method} Path={Path} CorrelationId={CorrelationId}",
            ResolveUserId(context.User), context.Request.Method, path, correlationId);""",
         """        var userBefore = ResolveUserId(context.User);
        _logger.LogInformation(
            "PHI_ACCESS: User={UserId} Method={Method} Path={Path} CorrelationId={CorrelationId}",
            userBefore, context.Request.Method, path, correlationId);"""),
        (MIDDLEWARE, """        var userId = ResolveUserId(context.User);
        if (userId == NoSubjectUser)""", """        var userId = userBefore;
        if (userId == NoSubjectUser)""")]),
    ("D3", "an unauthenticated request is recorded as anonymous", [(MIDDLEWARE,
        'public const string UnauthenticatedUser = "(unauthenticated)";', 'public const string UnauthenticatedUser = "anonymous";')]),
    ("D4", "an identity with no subject is recorded as unauthenticated", [(MIDDLEWARE,
        "        return NoSubjectUser;", "        return UnauthenticatedUser;")]),
    ("D5", "the claims of an identity that is not authenticated are read", [(MIDDLEWARE,
        "user?.Identities.Where(identity => identity.IsAuthenticated).ToList()", "user?.Identities.ToList()")]),
    ("D6", "the mapped name-identifier claim is not read", [(MIDDLEWARE,
        """
                ?? identity.FindFirst(ClaimTypes.NameIdentifier)?.Value;""", ";")]),
    ("D7", "a request header may name the user when there is no identity", [(MIDDLEWARE,
        """        var userId = ResolveUserId(context.User);
        if (userId == NoSubjectUser)""",
        f"""        var userId = ResolveUserId(context.User);
        if (userId == UnauthenticatedUser && {HEADER} is {{ Length: > 0 }} named)
            userId = named;
        if (userId == NoSubjectUser)""")]),
    ("D8", "a request refused with 401 is not recorded", [(MIDDLEWARE,
        """        var statusCode = context.Response.StatusCode;
""", """        var statusCode = context.Response.StatusCode;
        if (statusCode == StatusCodes.Status401Unauthorized)
            return;
""")]),
    ("D9", "a request refused with 403 is not recorded", [(MIDDLEWARE,
        """        var statusCode = context.Response.StatusCode;
""", """        var statusCode = context.Response.StatusCode;
        if (statusCode == StatusCodes.Status403Forbidden)
            return;
""")]),
    ("D10", "the event names the user a request header gives", [(MIDDLEWARE,
        "AuditEvent.PhiAccess(path, context.Request.Method, userId,", f"AuditEvent.PhiAccess(path, context.Request.Method, {HEADER} ?? userId,")]),
    ("D11", "the first log line names the user a request header gives", [(MIDDLEWARE,
        "ResolveUserId(context.User), context.Request.Method, path, correlationId);",
        f"{HEADER} ?? ResolveUserId(context.User), context.Request.Method, path, correlationId);")]),
    ("D12", "the completion log line names the user a request header gives", [(MIDDLEWARE,
        "userId, path, statusCode, (DateTime.UtcNow - startedAt).TotalMilliseconds);",
        f"{HEADER} ?? userId, path, statusCode, (DateTime.UtcNow - startedAt).TotalMilliseconds);")]),
    ("D13", "the subject is lower-cased before it is recorded", [(MIDDLEWARE,
        "                return subject;", "                return subject.ToLowerInvariant();")]),
    ("D14", "the record's time and correlation id are not stored", [(MIDDLEWARE,
        """                CorrelationId = correlationId,
                AccessedAt = accessedAt,""", """                CorrelationId = null,
                AccessedAt = default,""")]),
    ("D15", "the mapped name-identifier claim is preferred to sub", [(MIDDLEWARE,
        """            var subject = identity.FindFirst("sub")?.Value
                ?? identity.FindFirst(ClaimTypes.NameIdentifier)?.Value;""",
        """            var subject = identity.FindFirst(ClaimTypes.NameIdentifier)?.Value
                ?? identity.FindFirst("sub")?.Value;""")]),
    ("D16", "the line for a failed write does not name the user", [(MIDDLEWARE,
        "                userId, method, path, statusCode, correlationId);", '                "-", method, path, statusCode, correlationId);')]),
    ("O2", "a tenth service audits before authentication", [
        ("src/HealthQCopilot.Tenth/Program.cs", None, OLD_ORDER.format(audit="app.UseMiddleware<PhiAuditMiddleware>();"))]),
    ("O3", "a tenth service audits before authentication and registers the middleware by its type", [
        ("src/HealthQCopilot.Tenth/Program.cs", None, OLD_ORDER.format(audit="app.UseMiddleware(typeof(PhiAuditMiddleware));"))]),
    ("O4", "a tenth service audits before authentication and its name is added to the list of audited services", [
        ("src/HealthQCopilot.Tenth/Program.cs", None, OLD_ORDER.format(audit="app.UseMiddleware<PhiAuditMiddleware>();")),
        (ORDER_TESTS, '"PopulationHealth", "RevenueCycle", "Scheduling", "Voice",', '"PopulationHealth", "RevenueCycle", "Scheduling", "Tenth", "Voice",')]),
    ("O5", "a middleware that can refuse a request is put in front of authentication in one service", [
        (VOICE, "app.UseAuthentication();", "app.UseMiddleware<ConsentEnforcementMiddleware>();\napp.UseAuthentication();")]),
    ("O6", "one service registers the audit through an extension method in another file", [
        (VOICE, "app.UseMiddleware<PhiAuditMiddleware>();", "app.UsePhiAudit();"),
        ("src/HealthQCopilot.Infrastructure/Middleware/AuditExtensions.cs", None,
         "public static class AuditExtensions\n{\n    public static IApplicationBuilder UsePhiAudit(this IApplicationBuilder app) =>\n"
         "        app.UseMiddleware<PhiAuditMiddleware>();\n}\n")]),
    ("O7", "one service registers the audit after authorization", [
        (VOICE, "app.UseMiddleware<PhiAuditMiddleware>();\napp.UseAuthorization();", "app.UseAuthorization();\napp.UseMiddleware<PhiAuditMiddleware>();")]),
    ("O8", "one service registers authentication inside a condition", [
        (VOICE, "app.UseAuthentication();", "if (!app.Environment.IsDevelopment())\n{\n    app.UseAuthentication();\n}")]),
]


def dotnet(arguments: list[str], cwd: Path, repo: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1", HQ_REPO=str(repo))
    return subprocess.run(["dotnet", *arguments], cwd=cwd, env=env, capture_output=True, text=True)


def build_and_run(project: Path, repo: Path) -> tuple[str, list[str], list[str]]:
    """Returns (build error or '', names of the tests that passed, names of the tests that failed)."""
    out = repo / "tests" / "HealthQCopilot.Tests.Unit" / "bin" / "harness"
    try:
        build = dotnet(["build", "-c", "Release", "-o", str(out)], project, repo)
        if build.returncode != 0:
            errors = [line.strip() for line in build.stdout.splitlines() if " error " in line]
            return (errors[0] if errors else build.stdout.strip()[-400:]), [], []
        run = dotnet([str(out / "HealthQCopilot.Tests.Unit.dll")], repo, repo)
        passed = [line[6:] for line in run.stdout.splitlines() if line.startswith("PASS  ")]
        failed = [line[6:] for line in run.stdout.splitlines() if line.startswith("FAIL  ")]
        if not passed and not failed:
            return "the runner printed no result: " + (run.stdout + run.stderr).strip()[-400:], [], []
        return "", passed, failed
    finally:
        shutil.rmtree(out, ignore_errors=True)


def copy_needed(repo: Path, target: Path) -> None:
    programs = sorted(p.relative_to(repo).as_posix() for p in (repo / "src").glob("HealthQCopilot.*/Program.cs"))
    for relative in NEEDED + programs:
        (target / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / relative, target / relative)


def copy_at(repo: Path, ref: str, target: Path) -> None:
    """The needed files as they are at a commit; a file the commit does not have is left out."""
    listed = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, "src"], cwd=repo, capture_output=True, text=True)
    programs = sorted(line for line in listed.stdout.splitlines()
                      if line.startswith("src/HealthQCopilot.") and line.count("/") == 2 and line.endswith("/Program.cs"))
    for relative in NEEDED + programs:
        shown = subprocess.run(["git", "show", f"{ref}:{relative}"], cwd=repo, capture_output=True)
        if shown.returncode == 0:
            (target / relative).parent.mkdir(parents=True, exist_ok=True)
            (target / relative).write_bytes(shown.stdout)


def method(test: str) -> str:
    return test.split("(")[0].split(".")[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", required=True, type=Path, help="a clone of the healthcare repository")
    parser.add_argument("--at", help="run the tests as they are at this git ref, not the working copy")
    parser.add_argument("--seed", action="store_true", help="seed defects and see whether the tests catch them")
    parser.add_argument("--base", help="with --seed: a git ref whose service start-up order is also tried")
    options = parser.parse_args()
    repo = options.repo.resolve()

    with tempfile.TemporaryDirectory() as scratch:
        project = Path(scratch) / "harness"
        shutil.copytree(HERE, project, ignore=shutil.ignore_patterns("*.py", "*.md", "bin", "obj", "__pycache__"))

        if not options.seed:
            source = repo
            if options.at:
                source = Path(scratch) / "at"
                copy_at(repo, options.at, source)
            error, passed, failed = build_and_run(project, source)
            if error:
                print("did not compile:", error)
                return 1
            for test in passed:
                print("PASS ", test)
            for test in failed:
                print("FAIL ", test)
            print(f"\n{len(passed)} passed, {len(failed)} failed")
            return 0 if not failed else 1

        copy = Path(scratch) / "copy"
        copy_needed(repo, copy)
        error, passed, failed = build_and_run(project, copy)
        if error or failed:
            print("the unseeded copy does not pass, so seeding would say nothing:", error or failed)
            return 1
        print(f"Unseeded: {len(passed)} passed, 0 failed\n")

        survived = total = 0
        for label, what, edits in DEFECTS:
            shutil.rmtree(copy)
            copy_needed(repo, copy)
            for relative, old, new in edits:
                target = copy / relative
                if old is None:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(new, encoding="utf-8")
                    continue
                text = target.read_text(encoding="utf-8")
                if old not in text:
                    print(f"{label} {what}\n   could not be seeded: {relative} no longer contains the text it replaces")
                    return 1
                target.write_text(text.replace(old, new), encoding="utf-8")
            total += 1
            survived += report(label, what, *build_and_run(project, copy))

        if options.base:
            shutil.rmtree(copy)
            copy_needed(repo, copy)
            for program in sorted((copy / "src").glob("HealthQCopilot.*/Program.cs")):
                relative = program.relative_to(copy).as_posix()
                shown = subprocess.run(["git", "show", f"{options.base}:{relative}"], cwd=repo, capture_output=True)
                if shown.returncode == 0:
                    program.write_bytes(shown.stdout)
            total += 1
            survived += report("O1", f"the nine services start in the order they have at {options.base}", *build_and_run(project, copy))

        print(f"\n{total - survived} of {total} seeded defects caught")
        return 0 if survived == 0 else 1


def report(label: str, what: str, error: str, passed: list[str], failed: list[str]) -> int:
    """Prints one seeded defect's outcome; returns 1 when the tests did not catch it."""
    print(f"{label} {what}")
    if error:
        print("   NOT A TEST: the seeded copy does not compile:", error[-200:])
        return 1
    if failed:
        names = sorted({method(test) for test in failed})
        print(f"   caught by {len(failed)} test(s): " + ", ".join(names))
        return 0
    print("   NOT CAUGHT: every test still passes")
    return 1


if __name__ == "__main__":
    sys.exit(main())
