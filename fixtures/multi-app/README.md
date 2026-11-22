# multi-app fixture

A deliberately small system used by the kit's tests to prove the cross-application features (charter D8):
two services, one shared library, one database both services write to, and one external API.
All data is synthetic. Nothing here is meant to run in production.

| Node | What | Why it is here |
|---|---|---|
| `shop-orders`, `shop-billing` | Two services | Consumers of the shared library; both write to the same database |
| `shop-shared-lib` | Shared library | A change here must reach both services' owners |
| `shop-db` | PostgreSQL database | A shared store with two writers |
| `contract-payments-openapi` | External API contract | A dependency outside the repo |
