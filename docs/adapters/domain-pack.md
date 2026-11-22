# Adding a domain pack

A domain pack adds the mandatory spec sections and vocabulary for one regulated domain. `extensions/agentic-hipaa/` is the worked example.

## What a pack contains
```
extensions/agentic-<id>/
  extension.yml              a normal Spec Kit extension manifest; require the `agentic` extension
  pack.yml                   the pack definition the kit's checks read
  templates/<id>-sections.md the headings to copy into a spec
```

## pack.yml
| Field | Required | Meaning |
|---|---|---|
| `schema` | Yes | `agentic-pack/1` |
| `id` | Yes | The name used in `kit.yml` under `domain_packs` |
| `required_sections` | Yes | Headings every spec must contain, with content. `CK-DOMAIN-SECTIONS` enforces this in the Regulated profile |
| `controls` | Recommended | For each section: the reference it comes from and the question the author must answer |
| `classification` | Recommended | The data classification vocabulary, most restricted first. Used by the system map from slice 0.2 |
| `agreement` | Optional | The legal agreement the domain requires for data shared with an external party, and when |

## Rules
1. State at the top of `pack.yml` what the mapping is based on and the date it was checked, and that the pack is an engineering aid, not legal advice or a compliance certification.
2. Cite a specific clause for every required section. A section with no source should not be mandatory.
3. Keep sections answerable by an engineer. Ask what the change does to the protected data, not whether the organisation is compliant.
4. Allow "Not applicable" with a reason. An empty section fails; a reasoned "not applicable" passes.
5. Have someone qualified in the domain review the mapping before others rely on it, and record who and when in the pack.

## Installing and activating
```bash
specify extension add --dev path/to/extensions/agentic-<id>
python .specify/extensions/agentic/scripts/agentic.py init --profile regulated --repository owner/name --pack <id> --force
```
`init` copies `pack.yml` to `.specify/agentic/packs/<id>.yml`, which is the copy the checks read and the copy CODEOWNERS should protect.

## Testing a pack
Add a spec without one of the required sections and run `agentic.py check CK-DOMAIN-SECTIONS`. It must fail and name the section.
