# Edge Cases - Security and Compliance

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Waiter accesses cashier-only refund or settlement actions | Fraud or policy breach | Enforce strict role scopes and approval chains |
| Manual discount or complimentary item applied without reason | Revenue leakage and weak auditability | Require reason capture and manager approval above thresholds |
| Branch-level financial export includes unauthorized data | Accounting or privacy breach | Scope exports by branch and authorized role |
| Shared POS credentials are used across shifts | Accountability is lost | Require individual staff authentication and shift-linked sessions |
| Payment data is logged in operational traces | Compliance risk | Tokenize payment references and avoid storing sensitive card data |
