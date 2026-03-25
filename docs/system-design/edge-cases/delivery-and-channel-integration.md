# Edge Cases - Delivery and Channel Integration

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Delivery channel accepts an item that is locally unavailable | Service failure and refunds | Sync availability frequently and validate again before kitchen fire |
| Guest arrives for takeaway before order is ready | Queue and service pressure increase | Surface prep ETA and status touchpoints to staff and guest |
| Delivery order is canceled after kitchen prep began | Waste and accounting discrepancies | Route cancellation through compensation, wastage, and refund workflows |
| Same branch handles dine-in peak and delivery peak simultaneously | Kitchen prioritization becomes unstable | Support source-aware ticket priority policies |
| Channel commission data differs from settlement totals | Reconciliation confusion | Keep source-channel financial breakdowns explicit in reporting and exports |
