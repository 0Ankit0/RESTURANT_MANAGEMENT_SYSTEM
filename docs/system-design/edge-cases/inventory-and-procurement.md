# Edge Cases - Inventory and Procurement

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Stock deducted at order time but item later voided | Ingredient ledger becomes inaccurate | Reverse depletion through explicit compensating stock events |
| Goods received differ from purchase order quantities | Reconciliation and vendor trust issues | Keep discrepancy states and approval notes in receiving workflow |
| Physical count finds missing high-value ingredients | Shrinkage cannot be explained | Require stock count sessions with variance and adjustment approvals |
| Recipe changed while service is live | Consumption projections become inconsistent | Version recipes and control effective dates |
| Transfer between branches is delayed or partially received | Stock availability becomes misleading | Track in-transit states and receiving confirmation by branch |
