# Use Case Descriptions - Restaurant Management System

## UC-01: Reserve Table or Join Waitlist
**Primary Actor**: Guest / Customer or Host  
**Goal**: Secure dining access with predictable timing.

**Preconditions**:
- Branch is accepting reservations or waitlist entries.
- Seating policy and capacity rules are configured.

**Main Flow**:
1. Guest submits reservation or host creates a reservation/walk-in record.
2. System validates branch hours, table availability, and party-size rules.
3. Reservation or waitlist entry is created.
4. Guest and host see updated status and expected timing.

**Exceptions**:
- E1: No eligible seating window -> suggest alternative times or waitlist placement.
- E2: Reservation no-show threshold reached -> entry transitions according to policy.

---

## UC-02: Seat Table and Start Service
**Primary Actor**: Host / Reception

**Main Flow**:
1. Host selects an available table or merged table group.
2. System validates capacity, reservation linkage, and table readiness.
3. Table is marked occupied and assigned to a service zone/waiter.
4. Service timeline begins for the seated party.

---

## UC-03: Capture Order and Send to Kitchen
**Primary Actor**: Waiter / Captain

**Main Flow**:
1. Waiter opens the active table or takeaway order.
2. Waiter adds items, modifiers, notes, and course timing instructions.
3. System validates menu availability, pricing, and approval rules.
4. Order is saved and submitted.
5. Kitchen tickets are routed to the relevant prep stations.

**Exceptions**:
- E1: Item unavailable -> system prompts substitution or removal.
- E2: Approval needed for void/discount -> manager approval workflow begins.

---

## UC-04: Prepare Items and Coordinate Service
**Primary Actor**: Chef / Kitchen Staff

**Main Flow**:
1. Kitchen staff receives tickets by station and priority.
2. Staff mark items as accepted, in preparation, ready, or delayed.
3. System updates waiter visibility for service coordination.
4. Completed items move to pass/dispatch and then to served state.

**Exceptions**:
- E1: Ingredient shortage discovered -> staff flags stockout to front-of-house.
- E2: Item must be refired -> system records a controlled refire event.

---

## UC-05: Settle Bill and Close Cash Session
**Primary Actor**: Cashier / Accountant

**Main Flow**:
1. Cashier opens the bill for a table or takeaway order.
2. System calculates totals, taxes, charges, discounts, and prior partial payments.
3. Cashier accepts one or more payment methods.
4. System closes the settlement and updates order lifecycle.
5. At shift or day close, cashier balances the drawer and system produces settlement summaries and export data.

---

## UC-06: Procure Stock and Receive Goods
**Primary Actor**: Inventory / Purchase Manager

**Main Flow**:
1. Manager creates purchase request or purchase order from low-stock or planned demand.
2. Vendor and expected delivery details are recorded.
3. On receipt, manager records delivered quantities, variances, and quality notes.
4. Stock ledger is updated and discrepancies remain auditable.

---

## UC-07: Run Shift Scheduling and Attendance
**Primary Actor**: Branch Manager

**Main Flow**:
1. Branch manager publishes shifts for service, kitchen, cashier, and inventory roles.
2. Staff mark shift start/end or attendance is captured by workflow.
3. System shows branch coverage gaps and operational readiness.
4. Shift and day-close operations reference attendance and open sessions.

---

## UC-08: Configure Menus, Taxes, and Policies
**Primary Actor**: Admin

**Main Flow**:
1. Admin configures menu structures, taxes, payment methods, branch rules, and approval thresholds.
2. System validates conflicts and effective dates.
3. Updated policies are versioned and applied according to scope.
4. Audit logs capture actor, before/after state, and branch or global scope.
