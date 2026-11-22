// Shared by every service. A change here is a shared-component change.
function formatMoney(cents) {
  return (cents / 100).toFixed(2);
}
module.exports = { formatMoney };
