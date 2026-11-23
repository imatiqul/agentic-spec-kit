# Phase 7: tools used in the C4 walkthrough

- **Phase and date:** Phase 7, 2026-11-22
- **Upstream and reference:** spec-kit `v1.4.3`; healthcare repository `imatiqul/azure-ai-cloud-healthcare`, change for spec `004-audit-identity` on `main` at `8d04df3`
- **Requirement IDs exercised:** QLT-3, QLT-7, AGT-5
- **Assumptions:** the stand-ins behave as the real packages do for the calls the tests of spec 004 make
- **Unverified:** the healthcare solution was not restored, built or tested. Nothing here replaces that run

## `harness/`: the tests of spec 004 without the solution's packages

The healthcare solution needs packages from a registry that could not be reached from where the change was written. The harness is what could be done instead. It is not a substitute for `dotnet test`.

```bash
python examples/healthq/phase-7/harness/run.py --repo <healthcare clone>                      # the change's tests
python examples/healthq/phase-7/harness/run.py --repo <healthcare clone> --at 8d04df3         # the tests as they were
python examples/healthq/phase-7/harness/run.py --repo <healthcare clone> --seed --base 8d04df3 # seeded defects
```

| What is real | What is stood in for |
|---|---|
| `PhiAuditMiddleware.cs`, `TenantContextMiddleware.cs`, the two test files and the two order-test files, compiled unmodified | xUnit: four attributes and a reflection runner (`Shims/Xunit.cs`, `Runner.cs`) |
| The repository's `Directory.Build.props` (warnings are errors, code style enforced in the build) and `.editorconfig` | FluentAssertions: the assertion calls the tests make (`Shims/FluentAssertions.cs`) |
| ASP.NET Core 10: `ApplicationBuilder`, `UseAuthentication`, `UseAuthorization`, an authentication handler, `DefaultHttpContext` | NSubstitute: a recording proxy, received-call counts, `Returns` (`Shims/NSubstitute.cs`) |
| The nine `Program.cs` files, read as text by the order tests | EF Core's in-memory provider and `AuditDbContext`: rows kept per database name, visible after `SaveChangesAsync` (`Shims/EntityFramework.cs`, `Shims/AuditDbContext.cs`) |

What a pass does not show:
- that the solution builds: only six source files are compiled, not the nine services or the infrastructure project;
- that the real packages accept every call the tests make (the stand-ins accept what was written against them);
- what the xUnit analyzers say: the real build runs them with warnings as errors;
- anything about a database, a real token or a deployed service.

`--seed` makes one defect at a time in a temporary copy: sixteen in the middleware and seven in how a service registers it, and with `--base` it also puts the nine services back in their old order. It then says whether the tests catch each. Nine of the seeds are the author's; the others were added after two reviewing agents showed defects that passed every test. It is a check on the tests, not a mutation score.

The clone is only read. The build output goes to `tests/HealthQCopilot.Tests.Unit/bin/harness`, which the repository ignores, and is removed after each run.

## `rebuild_from_bundle.py`, `commit-map.md`, `pull-requests.md`: how the branches reached the owner's machine

The three branches were written in a workspace that cannot push. They were carried to the owner's machine as one git bundle and made again there, commit by commit, under his name:

```bash
git fetch origin main
python rebuild_from_bundle.py <healthcare repository> hq-branches.bundle hq-plan.json --check --identity-of 1b74f48
python rebuild_from_bundle.py <healthcare repository> hq-branches.bundle hq-plan.json --identity-of 1b74f48 --map hq-map.tsv
```

The script checks nothing out and moves no existing branch. It stops unless each branch ends in the tree the plan names, so the files are the ones that were reviewed. `commit-map.md` is its output as a table: the id each commit has in the records, and the id it has now. `pull-requests.md` holds a title and a description for each branch, for the owner to open as drafts.
