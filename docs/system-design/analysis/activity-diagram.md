# Activity Diagram - Restaurant Management System

## Guest-to-Settlement Flow

```mermaid
flowchart TD
    start([Guest wants service]) --> arrival{Reservation or walk-in?}
    arrival -- Reservation --> seat[Seat reserved table]
    arrival -- Walk-in --> wait{Table available?}
    wait -- No --> queue[Join waitlist and monitor status]
    wait -- Yes --> seat
    queue --> seat
    seat --> order[Waiter captures order]
    order --> validate{Items available and valid?}
    validate -- No --> adjust[Adjust order or substitute items]
    adjust --> order
    validate -- Yes --> kitchen[Route tickets to kitchen stations]
    kitchen --> prep[Prepare items and update status]
    prep --> ready[Mark ready / serve items]
    ready --> more{More items or requests?}
    more -- Yes --> order
    more -- No --> bill[Generate bill]
    bill --> settle[Collect payment and close settlement]
    settle --> close[Update sales, stock, and branch summaries]
    close --> end([Service completed])
```
