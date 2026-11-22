# Tasks: 004-audit-identity

Draft, waiting at gate G4. One task list for one pull request. `[P]` marks a task that may run beside the one before it.

- [ ] T001 Record the characterization run: the eleven existing tests in `tests/HealthQCopilot.Tests.Unit/Infrastructure/PhiAuditMiddlewareTests.cs`, at the base commit, before any other task @test-agent. Carries: AC-006
- [ ] T002 Change `src/HealthQCopilot.Infrastructure/Middleware/PhiAuditMiddleware.cs`: the user is the subject of the authenticated identity; a marker where there is none @backend-implementer. Carries: AC-002, AC-003, AC-004
- [ ] T003 [P] Put the audit middleware between authentication and authorization in `src/HealthQCopilot.Agents/Program.cs`, `src/HealthQCopilot.Fhir/Program.cs`, `src/HealthQCopilot.Identity/Program.cs`, `src/HealthQCopilot.Notifications/Program.cs`, `src/HealthQCopilot.Ocr/Program.cs`, `src/HealthQCopilot.PopulationHealth/Program.cs`, `src/HealthQCopilot.RevenueCycle/Program.cs`, `src/HealthQCopilot.Scheduling/Program.cs` and `src/HealthQCopilot.Voice/Program.cs`, each as the plan's table says @backend-implementer. Carries: AC-001
- [ ] T004 Rewrite the two tests that assert the old behaviour and add `tests/HealthQCopilot.Tests.Unit/Infrastructure/PhiAuditPipelineTests.cs` @test-agent. Carries: AC-002, AC-003, AC-004
- [ ] T005 [P] Add `tests/HealthQCopilot.Tests.Unit/Architecture/RequestPipelineOrderTests.cs` and the helper it uses, `tests/HealthQCopilot.Tests.Unit/Architecture/RequestPipelineOrder.cs` @test-agent. Carries: AC-001, AC-005
- [ ] T006 Verify the change against the spec, the constitution and the system map, with none of the author's notes @independent-verifier. Carries: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006
