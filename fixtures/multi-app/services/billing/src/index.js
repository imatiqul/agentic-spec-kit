const express = require('express');
const { formatMoney } = require('@shop/shared-lib');
const app = express();
// Writes to shop-db.invoices and reads shop-db.orders.
app.post('/invoices', async (req, res) => {
  // INSERT INTO invoices (tenant_id, order_id, amount_cents) VALUES ($1, $2, $3)
  res.json({ amount: formatMoney(req.body.amountCents) });
});
app.listen(3002);
