const express = require('express');
const { formatMoney } = require('@shop/shared-lib');
const app = express();
// Writes to shop-db.orders and calls the external payments API (contracts/payments-openapi.yaml).
app.post('/orders', async (req, res) => {
  // INSERT INTO orders (tenant_id, total_cents) VALUES ($1, $2)
  res.json({ total: formatMoney(req.body.totalCents) });
});
app.listen(3001);
