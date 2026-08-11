# 🚆 RailExpress Premier — Full-Stack Train Booking & Travel Platform

> **1-Hour Website Tournament Winner Submission**  
> A complete, production-grade commercial railway service platform with a functional Python Flask backend, SQLite relational database, interactive coach seat matrix, PNR ticket generator, backend age-restricted authentication, station stop timelines, travel itineraries, and hotel directory.

---

## 🌟 Key Features

1. **🏠 Real Railway Homepage & Branding**
   - Corporate transportation design (Deep Navy `#0b132b`, Emerald `#10b981`, Accent Blue `#3a86ff`, Cyber Cyan `#00f5d4`).
   - Dynamic Train Search bar (Origin Station, Destination Station, Journey Date, Passenger Count, Class, Search Engine).

2. **🚆 15+ Trains & 10+ Routes Database Network**
   - 15+ real train records (Vande Bharat Express, Rajdhani Express, Shatabdi Express, Tejas Express, Duronto Express, Himalayan Toy Train, etc.).
   - 10+ realistic routes covering Indian Railway corridors (Delhi, Kanpur, Lucknow, Varanasi, Mumbai, Agra, Bhopal, Jaipur, Goa, Kolkata, Puri, Shimla, Bangalore, Chennai).

3. **🕐 Detailed Station Schedules & Stop Timelines**
   - Visual timeline breakdown showing every intermediate stop sequence, arrival timestamp, departure timestamp, day number, and distance from origin.

4. **🔎 Train Search, Sorting & Filter Engine**
   - Real-time DB search for trains matching origin and destination stops where stop sequence is valid.
   - Filter & sort by: **Cheapest Fare**, **Fastest Duration**, **Earliest Departure**, and **Highest Seat Availability**.

5. **💺 Interactive Coach Seat Picker Grid**
   - Visual seat grid for coaches (`A1`, `B1`, `C1`, `EC1`, etc.).
   - Visual seat state indicators:
     - 🟢 **Available** (Green)
     - 🔵 **Selected** (Blue)
     - 🔴 **Occupied** (Red - Locked in database)
   - Double-booking prevention enforced atomically via SQL transactions.

6. **👤 User Accounts & Strict Backend Age Restriction**
   - Secure registration, login, logout, and session state.
   - **Backend Age Validation**: Registration requires Date of Birth. If user is `< 18 years old`, the backend API rejects registration with HTTP 400 error message.

7. **🎫 PNR Ticketing Engine & My Bookings**
   - Multi-passenger support per booking.
   - Generates unique 10-digit PNRs (e.g. `PNR-9840281`).
   - Itemized fare checkout (Base fare + 5% GST).
   - **Ticket Cancellation**: Cancelling a ticket immediately updates database status to `CANCELLED` and releases the seats back to available inventory.

8. **🗺 Tourist Travel Guides & Multi-Day Itineraries**
   - Comprehensive destination profiles (Varanasi, Lucknow, Jaipur, Goa, Agra, Shimla).
   - Day-by-day planned travel itineraries (e.g., 3-Day Lucknow Heritage & Culinary Tour, 3-Day Holy Varanasi Pilgrimage).

9. **🏨 Database-Driven Hotel Directory**
   - 15+ hotels across destinations with star ratings (`★ 4.9`), room pricing, location, contact, and amenities.

---

## 🗄 Database Schema (SQLite `railway.db`)

- `users` (id, full_name, email, password_hash, dob, phone, created_at)
- `stations` (id, code, name, city, state)
- `routes` (id, origin_station_id, dest_station_id, distance_km)
- `trains` (id, train_number, train_name, train_type, route_id, origin_station_id, dest_station_id, departure_time, arrival_time, duration, operating_days, base_fare, amenities)
- `train_stops` (id, train_id, stop_seq, station_id, arrival_time, departure_time, distance_km, day_number)
- `train_classes` (id, train_id, class_code, class_name, total_seats, price_multiplier)
- `seats` (id, train_id, class_code, coach_number, seat_number, seat_type)
- `bookings` (id, pnr, user_id, train_id, journey_date, class_code, total_fare, status, created_at)
- `booking_passengers` (id, booking_id, full_name, age, gender, seat_number)
- `seat_bookings` (id, train_id, journey_date, class_code, seat_number, booking_id) — *Unique constraint prevents double booking!*
- `destinations` (id, name, state, tagline, description, recommended_duration, best_time, local_transport, famous_food, tourist_tips, image_url)
- `attractions` (id, destination_id, name, category, description)
- `itineraries` (id, destination_id, title, duration_days, overview, day1, day2, day3, day4)
- `hotels` (id, destination_id, name, location, rating, price_per_night, room_types, amenities, description, image_url, contact, available_rooms)

---

## 🛠 Quick Start Guide

### 1. Requirements
- Python 3.10+ (Includes standard `sqlite3` library)
- Flask (`pip install Flask`)

### 2. Database Setup & Seeding
Run the seed script to create and populate `railway.db`:
```bash
python seed_db.py
```

### 3. Launch Application
Start the Flask web server:
```bash
python app.py
```

Open your browser and navigate to:  
👉 **http://127.0.0.1:5000**

---

## 🔑 Demo Accounts

| Email | Password | Date of Birth | Status |
|---|---|---|---|
| `rahul@example.com` | `Password123!` | `1995-04-12` (Age 31) | ✅ Active Demo User |
| `priya@example.com` | `Password123!` | `1998-11-20` (Age 27) | ✅ Active Demo User |
| *Under 18 Signup Test* | *Any* | *< 18 years ago* | ❌ Blocked by Backend |
