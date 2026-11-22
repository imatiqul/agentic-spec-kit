import json,glob,os,re,subprocess,sys
repo=sys.argv[1]; dest=sys.argv[2]; os.chdir(repo)
SHA=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
jl=lambda p: json.load(open(p,encoding='utf-8-sig'))
out=[]; w=out.append
w("# Draft system map — azure-ai-cloud-healthcare (HealthQ Copilot)")
w(f"# Discovered at commit {SHA}. Phase 1 draft; not yet confirmed by a human.")
w("# origin: derived = proven by the cited file; assumed = inferred, needs confirmation.")
w("# owner, tier and classification are PROPOSED and need confirming at the gate.")
w("schema: draft-0")
w("nodes:")
def node(id,type,origin,evidence,owner,tier,cls,note=None):
    w(f"  - id: {id}"); w(f"    type: {type}"); w(f"    origin: {origin}"); w(f"    evidence: \"{evidence}\"")
    w(f"    owner: {owner}"); w(f"    tier: {tier}"); w(f"    classification: \"{cls}\"")
    if note: w(f"    note: \"{note}\"")
svc={'Identity':('identity-service','identity-db','Critical'),'Voice':('voice-service','voice-db','High'),'Agents':('agent-service','agent-db','Critical'),
'Fhir':('fhir-service','fhir-db','Critical'),'Ocr':('ocr-service','ocr-db','High'),'Scheduling':('scheduling-service','scheduling-db','High'),
'Notifications':('notification-service','notification-db','High'),'PopulationHealth':('pophealth-service','pophealth-db','High'),'RevenueCycle':('revenue-service','revenue-db','High')}
for k,(s,db,t) in svc.items():
    node(s,'service','derived',f'src/HealthQCopilot.AppHost/Program.cs; src/HealthQCopilot.{k}/Program.cs','Backend',t,'PHI')
node('gateway','service','derived','src/HealthQCopilot.Gateway/Program.cs','Backend','Critical','PHI in transit','YARP reverse proxy; the only place authentication is required on all routes')
node('bff','service','derived','src/HealthQCopilot.BFF/Program.cs','Backend','High','PHI in transit','GraphQL (Hot Chocolate); no auth (finding H2)')
node('lib-domain','shared-library','derived','src/HealthQCopilot.Domain','Platform','High','none')
node('lib-infrastructure','shared-library','derived','src/HealthQCopilot.Infrastructure','Platform','Critical','none','auth, audit, tenant and persistence code shared by every service')
node('lib-service-defaults','shared-library','derived','src/HealthQCopilot.ServiceDefaults','Platform','High','none')
node('postgres','data-store','derived','src/HealthQCopilot.AppHost/Program.cs:6; infra/bicep/modules/postgres.bicep','Data Owner','Critical','PHI','engine: PostgreSQL')
for k,(s,db,t) in svc.items():
    node(db,'schema','derived','src/HealthQCopilot.AppHost/Program.cs:10-18','Data Owner',t,'PHI','database on postgres')
node('phi-audit-logs','schema-object','derived','src/HealthQCopilot.Infrastructure/Persistence/AuditDbContext.cs','Security & Compliance','Critical','PHI access metadata','table phi_audit_logs exists once per service database (9 copies); no tenant or patient column')
node('redis','data-store','derived','src/HealthQCopilot.AppHost/Program.cs:20; infra/bicep/modules/redis.bicep','Data Owner','High','unknown','cache; contents not derived')
node('qdrant','data-store','derived','src/HealthQCopilot.AppHost/Program.cs:28; src/HealthQCopilot.Agents/Rag/QdrantKnowledgeStore.cs','AI Engineer','High','clinical reference text','vector store')
node('cosmos','data-store','derived','src/HealthQCopilot.Agents/Program.cs:292; src/HealthQCopilot.Agents/Prompts/CosmosAgentPromptRegistry.cs','AI Engineer','High','unknown','containers not enumerated')
node('hapi-fhir','external-application','derived','src/HealthQCopilot.AppHost/Program.cs:23','Backend','High','PHI','HAPI FHIR server container v7.2.0')
node('pubsub','event-bus','derived','infra/dapr/components/pubsub.yaml; infra/bicep/modules/service-bus.bicep','DevOps/SRE','High','unknown','Dapr pub/sub; Azure Service Bus in cloud')
node('event-hubs-audit','event-stream','derived','src/HealthQCopilot.Infrastructure/Middleware/PhiAuditMiddleware.cs:85; infra/bicep/modules/event-hubs.bicep','Security & Compliance','Critical','PHI access metadata','optional dual-write of audit events')
for n,ev,owner,t,c,note in [
 ('entra-id','src/HealthQCopilot.Infrastructure/Auth/JwtBearerExtensions.cs','Security & Compliance','Critical','identity','identity provider; B2C module in infra/bicep/modules/b2c.bicep'),
 ('azure-openai','Microsoft.SemanticKernel.Connectors.OpenAI package reference','AI Engineer','Critical','PHI in prompts unless redacted','models referenced: gpt-4o, gpt-4o-mini, text-embedding-ada-002'),
 ('azure-speech','Microsoft.CognitiveServices.Speech package reference','AI Engineer','High','PHI (voice)',None),
 ('azure-document-intelligence','Azure.AI.DocumentIntelligence package reference','AI Engineer','High','PHI (documents)',None),
 ('azure-communication','Azure.Communication.Email and Sms package references','Backend','High','unknown',None),
 ('azure-web-pubsub','Azure.Messaging.WebPubSub package reference; infra/bicep/modules/web-pubsub.bicep','Backend','Medium','unknown',None),
 ('azure-app-configuration','Microsoft.Azure.AppConfiguration.AspNetCore; infra/bicep/feature-flags.bicep','DevOps/SRE','High','none','feature flags including PhiRedaction, RagRetrieval, HallucinationGuard'),
 ('key-vault','infra/bicep/modules/key-vault.bicep; infra/dapr/components/secretstore.yaml','Security & Compliance','Critical','secrets','secret references only; no values read'),
 ('apim','infra/apim/healthq-copilot-api.yaml; infra/bicep/modules/apim.bicep','DevOps/SRE','High','PHI in transit',None)]:
    node(n,'external-service','derived',ev,owner,t,c,note)
node('ai-triage-classifier','ai-component','derived','src/HealthQCopilot.Agents/Plugins/TriagePlugin.cs','AI Engineer','Critical','PHI','rule-based keyword matcher, not a model (finding C5)')
node('ai-rag-index','ai-component','derived','src/HealthQCopilot.Agents/Rag/','AI Engineer','Critical','clinical reference text','retrieval over qdrant; output concatenated into classifier input')
node('ai-prompts','ai-component','derived','src/HealthQCopilot.Agents/Prompts/','AI Engineer','High','none','prompt registry (in-memory or cosmos)')
node('ai-eval-golden-set','ai-component','derived','tests/HealthQCopilot.Tests.Eval/GoldenSets/triage.json; src/HealthQCopilot.Agents/Evaluation/golden-sets','AI Engineer','Critical','synthetic','5 cases in the tests golden set')
node('contract-apim-openapi','api-contract','derived','infra/apim/healthq-copilot-api.yaml','Solutions Architect','High','none','only committed API contract found')
node('contract-graphql','api-contract','assumed','src/HealthQCopilot.BFF/Types','Solutions Architect','High','none','code-first schema; no committed schema file')
fe=sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob('frontend/apps/*/package.json'))
for a in fe:
    node(a,'frontend','derived',f'frontend/apps/{a}/package.json','Frontend','High' if a in('shell','triage-mfe','voice-mfe','encounters-mfe') else 'Medium','PHI displayed')
pk={}
for p in glob.glob('frontend/packages/*/package.json'):
    pk[jl(p)['name']]=os.path.basename(os.path.dirname(p))
for name,dirn in sorted(pk.items()):
    node('pkg-'+dirn,'shared-package','derived',f'frontend/packages/{dirn}/package.json','Platform','High' if dirn in('auth-client','graphql-client') else 'Medium','none')
topics={}
g=subprocess.run(['grep','-rnoE',r'PublishEventAsync\(\s*"[^"]+",\s*"[^"]+"|\[Topic\("[^"]+",\s*"[^"]+"','--include=*.cs','src'],capture_output=True,text=True).stdout
for l in g.splitlines():
    m=re.match(r'src/HealthQCopilot\.([A-Za-z]+)/[^:]*:\d+:(PublishEventAsync\(|\[Topic\()\s*"pubsub",\s*"([^"]+)"',l)
    if m: topics.setdefault(m.group(3),{'pub':set(),'sub':set()})['pub' if 'Publish' in m.group(2) else 'sub'].add(m.group(1))
for t in sorted(topics):
    node('topic-'+t,'event','derived','PublishEventAsync calls and Topic attributes in src','Solutions Architect','High','unknown', None if topics[t]['pub'] else 'publisher not derived (27 publish calls use non-literal topic names)')
w("edges:")
def edge(a,rel,b,origin='derived',ev=None):
    w(f"  - {{from: {a}, rel: {rel}, to: {b}, origin: {origin}" + (f", evidence: \"{ev}\"" if ev else "") + "}")
lib={'Domain':'lib-domain','Infrastructure':'lib-infrastructure','ServiceDefaults':'lib-service-defaults'}
sid=lambda k: svc[k][0] if k in svc else k.lower()
for p in sorted(glob.glob('src/*/*.csproj')):
    k=os.path.basename(p)[len('HealthQCopilot.'):-len('.csproj')]
    if k in('AppHost',) : continue
    for r in re.findall(r'ProjectReference Include="[^"]*HealthQCopilot\.([A-Za-z]+)\.csproj"',open(p,encoding='utf-8-sig').read()):
        if r in lib: edge(lib.get(k) or sid(k),'builds-with',lib[r],ev=p)
for k,(s,db,t) in svc.items():
    edge(s,'owns',db,ev='src/HealthQCopilot.AppHost/Program.cs')
    edge(s,'writes','phi-audit-logs',ev=f'src/HealthQCopilot.{k}/Program.cs (AddHealthcareDb<AuditDbContext>)')
    edge(s,'authenticates-via','entra-id',ev=f'src/HealthQCopilot.{k}/Program.cs (AddHealthcareAuth)')
edge('identity-service','reads','phi-audit-logs',ev='src/HealthQCopilot.Identity/Endpoints/AuditExportEndpoints.cs (reads the identity-db copy only)')
edge('gateway','authenticates-via','entra-id',ev='src/HealthQCopilot.Gateway/Program.cs:10,49')
for s in ['pophealth-service','agent-service','revenue-service','scheduling-service','fhir-service','voice-service']:
    edge('bff','calls',s,ev='src/HealthQCopilot.BFF/Program.cs:11-39')
edge('gateway','calls','bff',ev='src/HealthQCopilot.Gateway/appsettings.json:78')
for s in [v[0] for v in svc.values()]:
    edge('gateway','calls',s,'assumed','YARP routes in src/HealthQCopilot.Gateway/appsettings.json; per-route targets not enumerated')
edge('agent-service','reads','qdrant',ev='src/HealthQCopilot.Agents/Rag/QdrantKnowledgeStore.cs')
edge('agent-service','writes','qdrant',ev='src/HealthQCopilot.Agents/Rag/KnowledgeIngestionService.cs')
edge('agent-service','writes','cosmos',ev='src/HealthQCopilot.Agents/Program.cs:292')
edge('agent-service','calls','azure-openai','assumed','Semantic Kernel OpenAI connector is referenced; call sites not traced')
edge('ai-rag-index','reads','qdrant',ev='src/HealthQCopilot.Agents/Rag/RagContextProvider.cs')
edge('ai-triage-classifier','reads','ai-rag-index',ev='src/HealthQCopilot.Agents/Services/TriageOrchestrator.cs:143-158')
edge('voice-service','calls','azure-speech','assumed'); edge('ocr-service','calls','azure-document-intelligence','assumed'); edge('notification-service','calls','azure-communication','assumed')
edge('fhir-service','calls','hapi-fhir','assumed','container declared in AppHost; client usage not traced')
for t in sorted(topics):
    for p in sorted(topics[t]['pub']): edge(sid(p),'publishes','topic-'+t)
    for s in sorted(topics[t]['sub']): edge(sid(s),'subscribes','topic-'+t)
for a in fe:
    if a!='shell': edge('shell','deploys-with',a,ev='frontend/apps/shell/vite.config.ts (module federation remotes)')
    d=jl(f'frontend/apps/{a}/package.json'); deps={**d.get('dependencies',{}),**d.get('devDependencies',{})}
    for name,dirn in sorted(pk.items()):
        if name in deps: edge(a,'builds-with','pkg-'+dirn,ev=f'frontend/apps/{a}/package.json')
edge('shell','calls','gateway','assumed','frontend API base URL not traced')
w("not_mapped:")
for x in ["Per-route gateway targets and APIM policies","Redis and Cosmos contents and their classification","Tables and columns inside each service database (only phi_audit_logs is mapped)","Infrastructure resources beyond the bicep module list","Publishers of triage.completed and escalation.required","Frontend to backend call paths","Kubernetes, Helm and Argo deployment topology"]:
    w(f"  - \"{x}\"")
open(dest,'w').write('\n'.join(out)+'\n')
