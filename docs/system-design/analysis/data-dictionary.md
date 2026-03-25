# Data Dictionary - Restaurant Management System

| Entity | Key Fields | Description |
|--------|------------|-------------|
| Branch | id, name, code, status, timezone | Restaurant branch or outlet |
| ServiceZone | id, branchId, name, type | Section or service area within branch |
| Table | id, branchId, zoneId, code, capacity, status | Physical dine-in table or table group |
| Reservation | id, branchId, guestName, partySize, slotTime, status | Guest reservation record |
| WaitlistEntry | id, branchId, guestName, partySize, queuePosition, status | Walk-in waitlist entry |
| StaffUser | id, branchId, role, status | Operational user account |
| Shift | id, branchId, roleType, startsAt, endsAt, status | Published staff shift |
| AttendanceRecord | id, shiftId, staffUserId, checkInAt, checkOutAt, status | Attendance or shift presence record |
| MenuItem | id, branchId, categoryId, name, price, status | Sellable menu item |
| ModifierGroup | id, menuItemId, name, selectionRules | Item customization rule set |
| Recipe | id, menuItemId, version, status | Ingredient usage definition |
| Ingredient | id, branchId, name, unit, currentStock, reorderLevel | Inventory ingredient |
| StockLedgerEntry | id, ingredientId, movementType, quantity, reason, recordedAt | Inventory movement history |
| PurchaseOrder | id, branchId, vendorId, status, orderedAt, receivedAt | Procurement order |
| GoodsReceipt | id, purchaseOrderId, recordedBy, varianceState | Receipt of purchased goods |
| Order | id, branchId, orderSource, tableId, status, waiterId, openedAt | Restaurant order container |
| OrderItem | id, orderId, menuItemId, quantity, notes, courseNo, status | Individual ordered line item |
| KitchenTicket | id, orderItemId, station, priority, status | Kitchen execution unit |
| Bill | id, orderId, subtotal, taxTotal, discountTotal, grandTotal, status | Bill generated from order |
| Settlement | id, billId, paymentMethod, amount, status, settledAt | Payment or split payment record |
| CashDrawerSession | id, branchId, cashierId, openedAt, closedAt, status | Cash session or drawer state |
| AccountingExport | id, branchId, periodRef, exportType, status | Operational accounting handoff |
| AuditLog | id, actorId, action, entityType, entityId, createdAt | Immutable operational history |
