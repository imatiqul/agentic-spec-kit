CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  total_cents INTEGER NOT NULL
);
CREATE TABLE invoices (
  id BIGSERIAL PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  order_id BIGINT NOT NULL REFERENCES orders(id),
  amount_cents INTEGER NOT NULL
);
