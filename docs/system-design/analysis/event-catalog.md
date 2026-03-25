# Event Catalog - Restaurant Management System

| Event | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| reservation.created | Reservation Service | Notification, Host Dashboard | New reservation captured |
| waitlist.promoted | Seating Service | Host Console, Guest Touchpoint | Waitlist entry moved toward seating |
| table.seated | Seating Service | POS, Reporting | Guest party seated |
| order.opened | POS Service | Kitchen Routing, Reporting | Service order started |
| order.item_added | POS Service | Kitchen Routing, Inventory Projection | Item added to order |
| kitchen.ticket_fired | Kitchen Service | KDS, Waiter Console | Item sent to preparation |
| kitchen.ticket_ready | Kitchen Service | Waiter Console, Reporting | Item ready for service |
| inventory.stock_low | Inventory Service | Branch Manager, Procurement | Stock threshold crossed |
| goods.received | Procurement Service | Inventory Ledger, Reporting | Purchase order receipt recorded |
| bill.closed | Billing Service | Settlement, Reporting | Bill finalized |
| settlement.completed | Settlement Service | Drawer Session, Accounting Export | Payment accepted and recorded |
| drawer.closed | Cashier Service | Reconciliation, Reporting | Cash session closed |
| accounting.export_generated | Accounting Export Service | External Accounting System | Export package prepared |
| shift.started | Workforce Service | Branch Dashboard | Staff shift in progress |
| shift.closed | Workforce Service | Day-Close Checks | Shift ended |
| admin.policy_changed | Admin Service | Audit, Rule Engines | Policy or config updated |
