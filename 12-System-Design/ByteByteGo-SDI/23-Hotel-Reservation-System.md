# Chapter 23: Hotel Reservation System

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/hotel-reservation-system)

Design a hotel reservation system like Booking.com, Expedia, or Marriott.

---

## Step 1 - Understand the problem and establish design scope

**Functional requirements:**
- Show hotel-related pages: hotel name, address, price, images, etc.
- Allow users to search for available rooms
- Handle room reservations
- Admin panel: add/remove/update hotel room information

**Non-functional requirements:**
- Support high concurrency: many customers booking the same hotel during peak season or events
- Moderate latency: acceptable for search and booking flows

**Back of the envelope estimation:**
- 5,000 hotels and 1 million rooms total
- Average occupancy: 70%
- Daily reservations: 1M * 0.7 = 700K
- Reservations per second: 700K / (24*3600) = ~8 TPS (low, but peak is much higher)

---

## Step 2 - High-level design

### API Design

1. **Hotel-related APIs**:
   - `GET /v1/hotels/{id}` — Get detailed info about a hotel
   - `POST /v1/hotels` — Add a new hotel (admin only)
   - `PUT /v1/hotels/{id}` — Update hotel info

2. **Room-related APIs**:
   - `GET /v1/hotels/{id}/rooms/{id}` — Get detailed info about room
   - `POST /v1/hotels/{id}/rooms` — Add a room

3. **Reservation APIs**:
   - `GET /v1/reservations` — Get reservation history
   - `GET /v1/reservations/{id}` — Get details of a reservation
   - `POST /v1/reservations` — Make a new reservation
   - `DELETE /v1/reservations/{id}` — Cancel a reservation

### Data model

**Hotel table**: hotel_id, name, address, city, state, country, description, star_rating

**Room table**: room_id, hotel_id, room_type, floor, number, price, status

**Reservation table**: reservation_id, hotel_id, room_id, guest_id, start_date, end_date, status, created_at

### High-level architecture

Client → CDN → Public API Gateway → Hotel Service, Rate Service, Reservation Service → Database

### Java Example – Reservation Service

```java
import java.time.LocalDate;
import java.util.*;
import java.util.concurrent.*;

public class ReservationService {
    private final Map<String, Reservation> reservations = new ConcurrentHashMap<>();
    // roomId-date → reserved (availability tracking)
    private final Set<String> bookedSlots = ConcurrentHashMap.newKeySet();

    record Reservation(String id, String roomId, String guestId,
                       LocalDate startDate, LocalDate endDate, String status) {}

    public synchronized String makeReservation(String roomId, String guestId,
                                                LocalDate start, LocalDate end) {
        // Check availability for all dates
        for (LocalDate d = start; d.isBefore(end); d = d.plusDays(1)) {
            String slot = roomId + "-" + d;
            if (bookedSlots.contains(slot)) {
                System.out.println("❌ Room " + roomId + " not available on " + d);
                return null;
            }
        }

        // Book all dates
        String reservationId = "RES-" + UUID.randomUUID().toString().substring(0, 8);
        for (LocalDate d = start; d.isBefore(end); d = d.plusDays(1)) {
            bookedSlots.add(roomId + "-" + d);
        }

        Reservation res = new Reservation(reservationId, roomId, guestId,
                                           start, end, "CONFIRMED");
        reservations.put(reservationId, res);
        System.out.println("✅ Reservation confirmed: " + reservationId);
        return reservationId;
    }

    public void cancelReservation(String reservationId) {
        Reservation res = reservations.get(reservationId);
        if (res != null) {
            for (LocalDate d = res.startDate(); d.isBefore(res.endDate()); d = d.plusDays(1)) {
                bookedSlots.remove(res.roomId() + "-" + d);
            }
            reservations.remove(reservationId);
            System.out.println("🗑️ Reservation cancelled: " + reservationId);
        }
    }

    public static void main(String[] args) {
        ReservationService service = new ReservationService();
        String res1 = service.makeReservation("ROOM-101", "GUEST-1",
            LocalDate.of(2024, 3, 15), LocalDate.of(2024, 3, 18));
        // Try to double-book
        service.makeReservation("ROOM-101", "GUEST-2",
            LocalDate.of(2024, 3, 16), LocalDate.of(2024, 3, 19));
        // Cancel and rebook
        service.cancelReservation(res1);
        service.makeReservation("ROOM-101", "GUEST-2",
            LocalDate.of(2024, 3, 16), LocalDate.of(2024, 3, 19));
    }
}
```

---

## Step 3 - Design deep dive

### Concurrency issues

When multiple users try to book the same room, we need to handle race conditions:

1. **Pessimistic locking**: Lock the record when selecting. Other transactions must wait. Simple but reduces throughput.
2. **Optimistic locking**: Use version numbers. Read with version, update with version check. If version mismatch, retry.
3. **Database constraints**: Use unique constraint on (room_id, date) to prevent double booking at DB level.

**Recommended**: Optimistic locking with database constraints for the reservation system.

### Scalability

- **Database sharding**: Shard by hotel_id
- **Caching**: Cache hotel/room info (read-heavy, rarely changes)
- **Microservices**: Hotel service, Room service, Reservation service, Payment service

### Data consistency

- Use **idempotency keys** to handle duplicate reservation requests
- Use **2-phase commit** or **saga pattern** for distributed transactions spanning reservation + payment

---

## Step 4 - Wrap up

Additional talking points:
- **Different room types**: availability per room type, not individual rooms
- **Pricing service**: Dynamic pricing based on demand
- **Payment processing**
- **Hotel search ranking**
- **Analytics and reporting dashboard**
