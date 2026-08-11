import sqlite3
import os
import hashlib
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'railway.db')

def init_db():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception as e:
            print(f"Notice: Could not remove old db: {e}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA foreign_keys = ON;")

    # 1. Users
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        dob TEXT NOT NULL,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # 2. Stations
    cur.execute('''
    CREATE TABLE IF NOT EXISTS stations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL
    );
    ''')

    # 3. Routes
    cur.execute('''
    CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_name TEXT NOT NULL,
        origin_station_id INTEGER NOT NULL,
        dest_station_id INTEGER NOT NULL,
        distance_km INTEGER NOT NULL,
        FOREIGN KEY(origin_station_id) REFERENCES stations(id),
        FOREIGN KEY(dest_station_id) REFERENCES stations(id)
    );
    ''')

    # 4. Trains
    cur.execute('''
    CREATE TABLE IF NOT EXISTS trains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_number TEXT UNIQUE NOT NULL,
        train_name TEXT NOT NULL,
        train_type TEXT NOT NULL,
        route_id INTEGER NOT NULL,
        origin_station_id INTEGER NOT NULL,
        dest_station_id INTEGER NOT NULL,
        departure_time TEXT NOT NULL,
        arrival_time TEXT NOT NULL,
        duration TEXT NOT NULL,
        operating_days TEXT NOT NULL,
        base_fare REAL NOT NULL,
        amenities TEXT NOT NULL,
        FOREIGN KEY(route_id) REFERENCES routes(id),
        FOREIGN KEY(origin_station_id) REFERENCES stations(id),
        FOREIGN KEY(dest_station_id) REFERENCES stations(id)
    );
    ''')

    # 5. Train Stops (Schedules)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS train_stops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_id INTEGER NOT NULL,
        stop_seq INTEGER NOT NULL,
        station_id INTEGER NOT NULL,
        arrival_time TEXT,
        departure_time TEXT,
        distance_km INTEGER NOT NULL,
        day_number INTEGER DEFAULT 1,
        FOREIGN KEY(train_id) REFERENCES trains(id),
        FOREIGN KEY(station_id) REFERENCES stations(id)
    );
    ''')

    # 6. Train Classes
    cur.execute('''
    CREATE TABLE IF NOT EXISTS train_classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_id INTEGER NOT NULL,
        class_code TEXT NOT NULL,
        class_name TEXT NOT NULL,
        total_seats INTEGER NOT NULL,
        price_multiplier REAL NOT NULL,
        FOREIGN KEY(train_id) REFERENCES trains(id)
    );
    ''')

    # 7. Seats Template
    cur.execute('''
    CREATE TABLE IF NOT EXISTS seats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_id INTEGER NOT NULL,
        class_code TEXT NOT NULL,
        coach_number TEXT NOT NULL,
        seat_number INTEGER NOT NULL,
        seat_type TEXT NOT NULL,
        FOREIGN KEY(train_id) REFERENCES trains(id)
    );
    ''')

    # 8. Bookings
    cur.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pnr TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        train_id INTEGER NOT NULL,
        journey_date TEXT NOT NULL,
        class_code TEXT NOT NULL,
        total_fare REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'CONFIRMED',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(train_id) REFERENCES trains(id)
    );
    ''')

    # 9. Booking Passengers
    cur.execute('''
    CREATE TABLE IF NOT EXISTS booking_passengers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        seat_number TEXT NOT NULL,
        FOREIGN KEY(booking_id) REFERENCES bookings(id) ON DELETE CASCADE
    );
    ''')

    # 10. Seat Bookings (Occupancy per Date)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS seat_bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_id INTEGER NOT NULL,
        journey_date TEXT NOT NULL,
        class_code TEXT NOT NULL,
        seat_number TEXT NOT NULL,
        booking_id INTEGER NOT NULL,
        FOREIGN KEY(train_id) REFERENCES trains(id),
        FOREIGN KEY(booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
        UNIQUE(train_id, journey_date, class_code, seat_number)
    );
    ''')

    # 11. Destinations
    cur.execute('''
    CREATE TABLE IF NOT EXISTS destinations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        state TEXT NOT NULL,
        tagline TEXT NOT NULL,
        description TEXT NOT NULL,
        recommended_duration TEXT NOT NULL,
        best_time TEXT NOT NULL,
        local_transport TEXT NOT NULL,
        famous_food TEXT NOT NULL,
        tourist_tips TEXT NOT NULL,
        image_url TEXT NOT NULL
    );
    ''')

    # 12. Attractions
    cur.execute('''
    CREATE TABLE IF NOT EXISTS attractions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        FOREIGN KEY(destination_id) REFERENCES destinations(id)
    );
    ''')

    # 13. Travel Itineraries
    cur.execute('''
    CREATE TABLE IF NOT EXISTS itineraries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        duration_days INTEGER NOT NULL,
        overview TEXT NOT NULL,
        day1 TEXT NOT NULL,
        day2 TEXT NOT NULL,
        day3 TEXT,
        day4 TEXT,
        FOREIGN KEY(destination_id) REFERENCES destinations(id)
    );
    ''')

    # 14. Hotels
    cur.execute('''
    CREATE TABLE IF NOT EXISTS hotels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        location TEXT NOT NULL,
        rating REAL NOT NULL,
        price_per_night REAL NOT NULL,
        room_types TEXT NOT NULL,
        amenities TEXT NOT NULL,
        description TEXT NOT NULL,
        image_url TEXT NOT NULL,
        contact TEXT NOT NULL,
        available_rooms INTEGER DEFAULT 15,
        FOREIGN KEY(destination_id) REFERENCES destinations(id)
    );
    ''')

    print("Tables created successfully.")

    # ------------------ SEED DATA ------------------

    # Seed Demo Users (Age >= 18)
    def hash_pw(pw):
        return hashlib.sha256(pw.encode('utf-8')).hexdigest()

    cur.executemany('''
    INSERT INTO users (full_name, email, password_hash, dob, phone) VALUES (?, ?, ?, ?, ?)
    ''', [
        ('Rahul Sharma', 'rahul@example.com', hash_pw('Password123!'), '1995-04-12', '+91 9876543210'),
        ('Priya Patel', 'priya@example.com', hash_pw('Password123!'), '1998-11-20', '+91 9812345678'),
        ('Amit Kumar', 'amit@example.com', hash_pw('Password123!'), '1990-08-15', '+91 9765432109')
    ])

    # Seed Stations (20+ stations)
    stations_data = [
        ('NDLS', 'New Delhi', 'Delhi', 'Delhi'),
        ('CNB', 'Kanpur Central', 'Kanpur', 'Uttar Pradesh'),
        ('LKO', 'Lucknow Charbagh', 'Lucknow', 'Uttar Pradesh'),
        ('BSB', 'Varanasi Junction', 'Varanasi', 'Uttar Pradesh'),
        ('AGC', 'Agra Cantt', 'Agra', 'Uttar Pradesh'),
        ('GWL', 'Gwalior Junction', 'Gwalior', 'Madhya Pradesh'),
        ('BPL', 'Bhopal Junction', 'Bhopal', 'Madhya Pradesh'),
        ('MMCT', 'Mumbai Central', 'Mumbai', 'Maharashtra'),
        ('CSMT', 'Chhatrapati Shivaji Maharaj Terminus', 'Mumbai', 'Maharashtra'),
        ('PUNE', 'Pune Junction', 'Pune', 'Maharashtra'),
        ('MAO', 'Madgaon Junction', 'Goa', 'Goa'),
        ('JP', 'Jaipur Junction', 'Jaipur', 'Rajasthan'),
        ('UDZ', 'Udaipur City', 'Udaipur', 'Rajasthan'),
        ('KLK', 'Kalka', 'Kalka', 'Haryana'),
        ('SML', 'Shimla', 'Shimla', 'Himachal Pradesh'),
        ('HWH', 'Howrah Junction', 'Kolkata', 'West Bengal'),
        ('PURI', 'Puri', 'Puri', 'Odisha'),
        ('BBS', 'Bhubaneswar', 'Bhubaneswar', 'Odisha'),
        ('SBC', 'KSR Bengaluru', 'Bengaluru', 'Karnataka'),
        ('MAS', 'Chennai Central', 'Chennai', 'Tamil Nadu')
    ]
    cur.executemany('INSERT INTO stations (code, name, city, state) VALUES (?, ?, ?, ?)', stations_data)

    # Get station IDs
    cur.execute('SELECT code, id FROM stations')
    stn_map = {row[0]: row[1] for row in cur.fetchall()}

    # Seed Routes (10+ routes)
    routes_data = [
        ('Delhi - Kanpur - Lucknow - Varanasi Line', stn_map['NDLS'], stn_map['BSB'], 780),
        ('Delhi - Agra - Bhopal - Mumbai Central Trunk', stn_map['NDLS'], stn_map['MMCT'], 1384),
        ('Delhi - Jaipur - Udaipur Express Corridor', stn_map['NDLS'], stn_map['UDZ'], 680),
        ('Mumbai CSMT - Ratnagiri - Madgaon Coastal Line', stn_map['CSMT'], stn_map['MAO'], 580),
        ('Delhi - Ambala - Kalka - Shimla Heritage Rail', stn_map['NDLS'], stn_map['SML'], 320),
        ('Kolkata Howrah - Bhubaneswar - Puri Odisha Line', stn_map['HWH'], stn_map['PURI'], 500),
        ('Bengaluru - Chennai Fast Track Corridor', stn_map['SBC'], stn_map['MAS'], 360),
        ('Mumbai CSMT - Pune Express Highway', stn_map['CSMT'], stn_map['PUNE'], 190),
        ('Delhi - Gwalior - Agra Return Corridor', stn_map['NDLS'], stn_map['GWL'], 320),
        ('Kolkata Howrah - Delhi Main Trunk', stn_map['HWH'], stn_map['NDLS'], 1440)
    ]
    cur.executemany('''
    INSERT INTO routes (route_name, origin_station_id, dest_station_id, distance_km)
    VALUES (?, ?, ?, ?)
    ''', routes_data)

    cur.execute('SELECT id, route_name FROM routes')
    routes_list = cur.fetchall()

    # Seed Trains (16 trains)
    trains_data = [
        ('22436', 'Vande Bharat Express', 'Semi-High Speed', 1, stn_map['NDLS'], stn_map['BSB'], '06:00 AM', '02:00 PM', '8h 00m', 'Mon,Tue,Wed,Fri,Sat,Sun', 1750.0, 'WiFi, Gourmet Catering, Reclining Seats, Panoramic Windows, Charging Ports'),
        ('12424', 'New Delhi - Dibrugarh Rajdhani Express', 'Superfast Premium', 1, stn_map['NDLS'], stn_map['BSB'], '04:10 PM', '01:00 AM', '8h 50m', 'Daily', 1450.0, 'Complimentary Meals, Clean Bedding, AC, Reading Lamp'),
        ('12004', 'Lucknow Shatabdi Express', 'Superfast Express', 1, stn_map['NDLS'], stn_map['LKO'], '06:10 AM', '12:40 PM', '6h 30m', 'Daily', 1120.0, 'Breakfast Included, Executive Seating, Clean Restrooms'),
        ('82502', 'Lucknow - New Delhi Tejas Express', 'Corporate Premium', 1, stn_map['LKO'], stn_map['NDLS'], '03:35 PM', '10:05 PM', '6h 30m', 'Mon,Wed,Thu,Fri,Sat,Sun', 1350.0, 'Hostess Service, Onboard WiFi, Travel Insurance, Free Tea/Coffee'),
        ('12952', 'Mumbai Rajdhani Express', 'Superfast Premium', 2, stn_map['NDLS'], stn_map['MMCT'], '04:55 PM', '08:35 AM', '15h 40m', 'Daily', 2850.0, 'Three-Course Meals, Luxury Bedding, Attendant, Power Outlets'),
        ('12954', 'August Kranti Rajdhani', 'Superfast Premium', 2, stn_map['NDLS'], stn_map['MMCT'], '05:15 PM', '10:05 AM', '16h 50m', 'Daily', 2650.0, 'Full Board Catering, Air Conditioned, Linen Included'),
        ('12015', 'Ajmer Shatabdi Express', 'Superfast Express', 3, stn_map['NDLS'], stn_map['JP'], '06:00 AM', '10:40 AM', '4h 40m', 'Daily', 890.0, 'Morning Snacks, Tea/Coffee, Executive Chair Car'),
        ('20972', 'Udaipur City Superfast', 'Express', 3, stn_map['NDLS'], stn_map['UDZ'], '11:00 PM', '07:30 AM', '8h 30m', 'Tue,Fri,Sun', 950.0, 'Charging Sockets, Bedding, Clean Coaches'),
        ('10103', 'Mandovi Express', 'Scenic Express', 4, stn_map['CSMT'], stn_map['MAO'], '07:10 AM', '07:00 PM', '11h 50m', 'Daily', 780.0, 'Pantry Car, Coastal Views, Reclining Seats'),
        ('12134', 'Mumbai CSMT Express', 'Superfast Express', 4, stn_map['MAO'], stn_map['CSMT'], '02:15 PM', '04:35 AM', '14h 20m', 'Daily', 820.0, 'Pantry Service, AC Sleeper Options'),
        ('12011', 'Kalka Shatabdi Express', 'Superfast Express', 5, stn_map['NDLS'], stn_map['KLK'], '07:40 AM', '11:45 AM', '4h 05m', 'Daily', 740.0, 'Breakfast, Panoramic Windows, Air Conditioned'),
        ('52455', 'Himalayan Queen Toy Train', 'Heritage Narrow Gauge', 5, stn_map['KLK'], stn_map['SML'], '12:10 PM', '05:20 PM', '5h 10m', 'Daily', 450.0, 'Heritage Wooden Interiors, Mountain Scenic Route'),
        ('22302', 'Howrah - Puri Vande Bharat', 'Semi-High Speed', 6, stn_map['HWH'], stn_map['PURI'], '06:10 AM', '12:35 PM', '6h 25m', 'Mon,Tue,Thu,Fri,Sat,Sun', 1260.0, 'Onboard Catering, High Speed WiFi, Reclining Seats'),
        ('12802', 'Purushottam Express', 'Superfast', 6, stn_map['HWH'], stn_map['PURI'], '10:30 PM', '05:30 AM', '7h 00m', 'Daily', 650.0, 'Sleeper & AC Coaches, Pantry Car'),
        ('12640', 'Brindavan Express', 'Superfast', 7, stn_map['SBC'], stn_map['MAS'], '03:00 PM', '09:10 PM', '6h 10m', 'Daily', 560.0, 'AC Chair Car, Pantry Service, Charging Ports'),
        ('12124', 'Deccan Queen Express', 'Superfast Heritage', 8, stn_map['PUNE'], stn_map['CSMT'], '07:15 AM', '10:25 AM', '3h 10m', 'Daily', 340.0, 'Dining Car, Famous Cutlets Service, Express Route')
    ]

    cur.executemany('''
    INSERT INTO trains (train_number, train_name, train_type, route_id, origin_station_id, dest_station_id, departure_time, arrival_time, duration, operating_days, base_fare, amenities)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', trains_data)

    cur.execute('SELECT id, train_number, origin_station_id, dest_station_id FROM trains')
    trains_dict = {row[1]: row[0] for row in cur.fetchall()}

    # Seed Train Stops (Detailed Intermediate Station Schedules for Schedule Timeline)
    stops_data = [
        # Train 22436 Vande Bharat (Delhi -> Kanpur -> Lucknow -> Varanasi)
        (trains_dict['22436'], 1, stn_map['NDLS'], None, '06:00 AM', 0, 1),
        (trains_dict['22436'], 2, stn_map['CNB'], '10:08 AM', '10:10 AM', 440, 1),
        (trains_dict['22436'], 3, stn_map['LKO'], '11:45 AM', '11:50 AM', 510, 1),
        (trains_dict['22436'], 4, stn_map['BSB'], '02:00 PM', None, 780, 1),

        # Train 12424 Rajdhani (Delhi -> Kanpur -> Lucknow -> Varanasi)
        (trains_dict['12424'], 1, stn_map['NDLS'], None, '04:10 PM', 0, 1),
        (trains_dict['12424'], 2, stn_map['CNB'], '09:20 PM', '09:25 PM', 440, 1),
        (trains_dict['12424'], 3, stn_map['LKO'], '10:50 PM', '11:00 PM', 510, 1),
        (trains_dict['12424'], 4, stn_map['BSB'], '01:00 AM', None, 780, 2),

        # Train 12004 Shatabdi (Delhi -> Kanpur -> Lucknow)
        (trains_dict['12004'], 1, stn_map['NDLS'], None, '06:10 AM', 0, 1),
        (trains_dict['12004'], 2, stn_map['CNB'], '11:20 AM', '11:25 AM', 440, 1),
        (trains_dict['12004'], 3, stn_map['LKO'], '12:40 PM', None, 510, 1),

        # Train 12952 Mumbai Rajdhani (Delhi -> Agra -> Gwalior -> Bhopal -> Mumbai Central)
        (trains_dict['12952'], 1, stn_map['NDLS'], None, '04:55 PM', 0, 1),
        (trains_dict['12952'], 2, stn_map['AGC'], '06:50 PM', '06:52 PM', 195, 1),
        (trains_dict['12952'], 3, stn_map['GWL'], '08:15 PM', '08:17 PM', 313, 1),
        (trains_dict['12952'], 4, stn_map['BPL'], '11:40 PM', '11:45 PM', 701, 1),
        (trains_dict['12952'], 5, stn_map['MMCT'], '08:35 AM', None, 1384, 2),

        # Train 12015 Ajmer Shatabdi (Delhi -> Jaipur)
        (trains_dict['12015'], 1, stn_map['NDLS'], None, '06:00 AM', 0, 1),
        (trains_dict['12015'], 2, stn_map['JP'], '10:40 AM', None, 308, 1),

        # Train 10103 Mandovi Express (Mumbai CSMT -> Madgaon)
        (trains_dict['10103'], 1, stn_map['CSMT'], None, '07:10 AM', 0, 1),
        (trains_dict['10103'], 2, stn_map['PUNE'], '10:30 AM', '10:35 AM', 190, 1),
        (trains_dict['10103'], 3, stn_map['MAO'], '07:00 PM', None, 580, 1),

        # Train 12011 Kalka Shatabdi (Delhi -> Kalka)
        (trains_dict['12011'], 1, stn_map['NDLS'], None, '07:40 AM', 0, 1),
        (trains_dict['12011'], 2, stn_map['KLK'], '11:45 AM', None, 300, 1),

        # Train 52455 Toy Train (Kalka -> Shimla)
        (trains_dict['52455'], 1, stn_map['KLK'], None, '12:10 PM', 0, 1),
        (trains_dict['52455'], 2, stn_map['SML'], '05:20 PM', None, 96, 1),

        # Train 22302 Howrah Vande Bharat (Howrah -> Bhubaneswar -> Puri)
        (trains_dict['22302'], 1, stn_map['HWH'], None, '06:10 AM', 0, 1),
        (trains_dict['22302'], 2, stn_map['BBS'], '10:45 AM', '10:50 AM', 436, 1),
        (trains_dict['22302'], 3, stn_map['PURI'], '12:35 PM', None, 500, 1)
    ]

    cur.executemany('''
    INSERT INTO train_stops (train_id, stop_seq, station_id, arrival_time, departure_time, distance_km, day_number)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', stops_data)

    # Seed Train Classes & Seats Matrix
    classes_def = [
        ('EC', 'Executive Chair Car', 30, 1.8),
        ('1A', 'AC First Class', 24, 2.2),
        ('2A', 'AC 2-Tier', 36, 1.5),
        ('3A', 'AC 3-Tier', 48, 1.0),
        ('CC', 'AC Chair Car', 40, 0.9),
        ('SL', 'Sleeper Class', 60, 0.5)
    ]

    cur.execute('SELECT id FROM trains')
    all_train_ids = [row[0] for row in cur.fetchall()]

    for tid in all_train_ids:
        # Add 3 representative classes per train
        for ccode, cname, cap, mult in classes_def[:4]:
            cur.execute('''
            INSERT INTO train_classes (train_id, class_code, class_name, total_seats, price_multiplier)
            VALUES (?, ?, ?, ?, ?)
            ''', (tid, ccode, cname, cap, mult))

            # Generate seats matrix for interactive seat selection
            coach_prefix = ccode + "1"
            seat_types = ['Window', 'Aisle', 'Middle']
            for snum in range(1, 25): # 24 interactive seats per class
                stype = seat_types[snum % 3]
                cur.execute('''
                INSERT INTO seats (train_id, class_code, coach_number, seat_number, seat_type)
                VALUES (?, ?, ?, ?, ?)
                ''', (tid, ccode, coach_prefix, snum, stype))

    # Seed Occupied Seats for Demonstration (so visual states show 🟢 Available, 🔵 Selected, 🔴 Occupied)
    today_str = date.today().strftime('%Y-%m-%d')
    tomorrow_str = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')

    # Seed a sample booking
    cur.execute('''
    INSERT INTO bookings (pnr, user_id, train_id, journey_date, class_code, total_fare, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('PNR-9840281', 1, 1, tomorrow_str, 'EC', 3675.0, 'CONFIRMED'))
    sample_booking_id = cur.lastrowid

    cur.execute('''
    INSERT INTO booking_passengers (booking_id, full_name, age, gender, seat_number)
    VALUES (?, ?, ?, ?, ?)
    ''', (sample_booking_id, 'Rahul Sharma', 29, 'Male', '4'))

    cur.execute('''
    INSERT INTO seat_bookings (train_id, journey_date, class_code, seat_number, booking_id)
    VALUES (?, ?, ?, ?, ?)
    ''', (1, tomorrow_str, 'EC', '4', sample_booking_id))

    cur.execute('''
    INSERT INTO seat_bookings (train_id, journey_date, class_code, seat_number, booking_id)
    VALUES (?, ?, ?, ?, ?)
    ''', (1, tomorrow_str, 'EC', '5', sample_booking_id))

    # 11. Seed Tourist Destinations (6 Destinations)
    destinations_data = [
        ('Varanasi', 'Uttar Pradesh', 'The Ancient Spiritual Capital of India', 
         'Varanasi, one of the world\'s oldest continually inhabited cities, sits along the sacred River Ganges. Renowned for its iconic ghats, evening Ganga Aarti ceremonies, historic temples, and rich classical music heritage.',
         '3 Days / 2 Nights', 'October to March', 'E-Rickshaws, Auto Rickshaws, Boat Rides',
         'Banarasi Paan, Kachori Sabzi, Malaiyo, Rabri, Choora Matar',
         'Attend evening Ganga Aarti at Dashashwamedh Ghat by 6:00 PM. Book boat rides early in the morning for sunrises.',
         'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=80'),

        ('Lucknow', 'Uttar Pradesh', 'The Royal City of Nawabs & Architecture',
         'Lucknow is celebrated for its grand Awadhi architecture, courtly etiquette, classical music, fine Chikan embroidery, and legendary culinary delights.',
         '3 Days / 2 Nights', 'October to March', 'Metro, Auto Rickshaws, App Cabs',
         'Tunday Kababi Galouti Kebab, Basket Chaat, Lucknowi Biryani, Sheermal',
         'Bara Imambara features the world\'s largest unsupported vaulted hall. Explore Aminabad market for handcrafted Chikan suits.',
         'https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1200&q=80'),

        ('Jaipur', 'Rajasthan', 'The Majestic Pink City & Fort Heritage',
         'The capital of Rajasthan, Jaipur forms the Golden Triangle along with Delhi and Agra. Home to magnificent hilltop forts, royal palaces, vibrant bazaars, and opulent heritage hotels.',
         '3 Days / 2 Nights', 'November to February', 'Auto Rickshaws, Low Floor Buses, Metro',
         'Dal Baati Churma, Pyaaz Kachori, Ghewar, Laal Maas',
         'Visit Amer Fort early in the morning to avoid long queues. Photography is breathtaking from Nahargarh Fort during sunset.',
         'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80'),

        ('Goa', 'Goa', 'Pearl of the Orient & Coastal Paradise',
         'Goa combines sun-kissed golden beaches, UNESCO World Heritage Portuguese churches, spice plantations, vibrant nightlife, and mouth-watering Konkani seafood.',
         '4 Days / 3 Nights', 'November to February', 'Scooter Rental, Taxi, Local Buses',
         'Goan Fish Curry Rice, Bebinca, Pork Vindaloo, Prawn Balchão, Feni',
         'Rent a scooter for fast local navigation. North Goa is famous for nightlife, South Goa for serene peaceful beaches.',
         'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=80'),

        ('Agra', 'Uttar Pradesh', 'City of the Eternal Taj Mahal',
         'Agra is world-famous as the home of the Taj Mahal, a UNESCO World Heritage Site and one of the Seven Wonders of the World. Agra also houses the majestic Agra Fort and Fatehpur Sikri.',
         '2 Days / 1 Night', 'October to March', 'Auto Rickshaws, Battery Rickshaws, Taxis',
         'Agra Petha (Paan Petha, Kesar Petha), Bedai and Jalebi, Mughlai Kebabs',
         'The Taj Mahal is closed on Fridays. Visit at sunrise for fewer crowds and soft golden lighting.',
         'https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1200&q=80'),

        ('Shimla', 'Himachal Pradesh', 'Queen of the Hills & Pine Forests',
         'Set amid snow-capped Himalayan peaks and oak forests, Shimla is a legendary hill station featuring Victorian architecture, the Mall Road, Ridge, and the historic Toy Train line.',
         '3 Days / 2 Nights', 'March to June & Dec for Snow', 'Local Buses, Taxis, Walking on Mall Road',
         'Siddu, Chha Gosht, Babru, Madra, Fresh Mountain Apples & Bakery Items',
         'Vehicles are not allowed on Mall Road; wear comfortable walking shoes. Ride the heritage Kalka-Shimla Toy Train for scenic views.',
         'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=1200&q=80')
    ]

    cur.executemany('''
    INSERT INTO destinations (name, state, tagline, description, recommended_duration, best_time, local_transport, famous_food, tourist_tips, image_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', destinations_data)

    cur.execute('SELECT id, name FROM destinations')
    dest_map = {row[1]: row[0] for row in cur.fetchall()}

    # 12. Seed Attractions
    attractions_data = [
        (dest_map['Varanasi'], 'Dashashwamedh Ghat', 'Spiritual & Cultural', 'The most vibrant ghat where grand evening Ganga Aarti takes place daily with brass lamps and chants.'),
        (dest_map['Varanasi'], 'Kashi Vishwanath Temple', 'Heritage Religious', 'One of the twelve sacred Jyotirlingas, recently renovated into the magnificent Kashi Vishwanath Corridor.'),
        (dest_map['Varanasi'], 'Sarnath', 'Archaeological Site', 'Where Lord Buddha gave his first sermon after attaining enlightenment. Home to Dhamek Stupa and Ashoka Pillar.'),
        
        (dest_map['Lucknow'], 'Bara Imambara & Bhool Bhulaiya', 'Historical Monument', 'Famous 18th-century architectural marvel featuring an intricate labyrinth maze and unsupported grand hall.'),
        (dest_map['Lucknow'], 'Rumi Darwaza', 'Architectural Gateway', 'A 60-foot tall grand gateway standing as the majestic symbol of Lucknow heritage.'),
        (dest_map['Lucknow'], 'Hazratganj Market', 'Shopping & Dining', 'The heart of Lucknow for shopping, Victorian architecture strolling, and famous chaat sampling.'),

        (dest_map['Jaipur'], 'Amer Fort', 'Royal Palace Fort', 'A grand hilltop fortress featuring Rajput-Mughal architecture, Sheesh Mahal (Mirror Palace), and courtyards.'),
        (dest_map['Jaipur'], 'Hawa Mahal', 'Architectural Icon', 'The iconic 5-story Pink Palace of Winds built with 953 honeycombed jharokha windows.'),
        (dest_map['Jaipur'], 'City Palace & Jantar Mantar', 'Royal Museum & Astronomical Observatory', 'The residence of the Royal family of Jaipur and UNESCO astronomical observatory.'),

        (dest_map['Goa'], 'Baga & Calangute Beach', 'Coastal Beach', 'Energetic beaches offering water sports, beach shacks, seafood, and evening sunset music.'),
        (dest_map['Goa'], 'Basilica of Bom Jesus', 'UNESCO Heritage Church', 'Historic 16th-century church in Old Goa holding the mortal remains of St. Francis Xavier.'),
        (dest_map['Goa'], 'Dudhsagar Waterfalls', 'Nature & Adventure', 'A majestic four-tiered waterfall cascading down 310 meters amidst lush Western Ghats greenery.')
    ]
    cur.executemany('''
    INSERT INTO attractions (destination_id, name, category, description)
    VALUES (?, ?, ?, ?)
    ''', attractions_data)

    # 13. Seed Planned Travel Itineraries
    itineraries_data = [
        (dest_map['Lucknow'], '3-Day Lucknow Heritage & Culinary Experience', 3,
         'Explore the architectural splendor and royal gastronomy of the City of Nawabs.',
         'Day 1: Arrive via Lucknow Shatabdi at 12:40 PM. Check in at hotel. Evening visit to Hazratganj market and taste famous Basket Chaat.',
         'Day 2: Morning tour of Bara Imambara and its famous Bhool Bhulaiya labyrinth. Photo stop at Rumi Darwaza. Royal Awadhi dinner featuring Galouti Kebabs at Aminabad.',
         'Day 3: Visit Chhatar Manzil and British Residency. Shopping for Chikankari handicrafts. Return train departing in evening.', None),

        (dest_map['Varanasi'], '3-Day Holy Varanasi & Sarnath Pilgrimage', 3,
         'A soul-stirring spiritual journey along the ancient ghats of the River Ganges.',
         'Day 1: Morning arrival on Vande Bharat Express. Hotel check-in. Afternoon walking tour of heritage alleys. Attend 6:00 PM Ganga Aarti at Dashashwamedh Ghat.',
         'Day 2: Early morning boat ride from Assi Ghat to Manikarnika Ghat during sunrise. Morning darshan at Kashi Vishwanath Corridor. Excursion to Sarnath Stupa in the afternoon.',
         'Day 3: Breakfast featuring famous Kachori Sabzi and Jalebi. Shopping for handcrafted Banarasi silk saris. Evening return train.', None),

        (dest_map['Jaipur'], '4-Day Royal Jaipur Golden Triangle Tour', 4,
         'Immerse yourself in Rajasthan\'s pink sandstone palaces, hill forts, and royal bazaars.',
         'Day 1: Arrive at Jaipur Junction via Ajmer Shatabdi. Check into heritage hotel. Visit Hawa Mahal and Johari Bazaar in evening.',
         'Day 2: Full day excursion to Amer Fort, Jaigarh Fort, and Sheesh Mahal. Sunset dinner overviewing Jaipur city from Nahargarh Fort.',
         'Day 3: Tour City Palace Museum, Jantar Mantar Observatory, and Jal Mahal. Enjoy traditional Dal Baati Churma dinner.',
         'Day 4: Morning souvenir shopping at Bapu Bazaar. Return train back to Delhi.')
    ]
    cur.executemany('''
    INSERT INTO itineraries (destination_id, title, duration_days, overview, day1, day2, day3, day4)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', itineraries_data)

    # 14. Seed Hotels (15+ Hotels across destinations)
    hotels_data = [
        (dest_map['Varanasi'], 'BrijRama Palace - Heritage Hotel on Ghats', 'Darbhanga Ghat, Varanasi', 4.9, 8500.0, 'Luxury Suite, River View Deluxe, Heritage Room', 'River View, Elevator, Fine Dining, Classical Music Evenings, Spa', '18th-century palace hotel overlooking the holy Ganga river.', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80', '+91 542 2400100', 12),
        (dest_map['Varanasi'], 'Taj Ganges Varanasi', 'Nadesar Palace Grounds, Varanasi', 4.8, 6200.0, 'Executive Suite, Deluxe Garden View', 'Swimming Pool, Spa, Buffet Breakfast, Gardens, Valet Parking', 'Luxury 5-star hotel set amidst 12 acres of lush green gardens.', 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80', '+91 542 6660000', 18),
        (dest_map['Varanasi'], 'Hotel Surya Heritage', 'Cantonment, Varanasi', 4.5, 3100.0, 'Deluxe Room, Family Suite', 'Free WiFi, Rooftop Restaurant, Airport Shuttle, AC', 'Charming heritage property close to railway station.', 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80', '+91 542 2508412', 20),

        (dest_map['Lucknow'], 'Taj Mahal Lucknow', 'Vipin Khand, Gomti Nagar, Lucknow', 4.9, 7800.0, 'Presidential Suite, Deluxe River View', 'Infinity Pool, Awadhi Fine Dining, Gym, Spa, Executive Lounge', 'Palatial 5-star hotel situated on the banks of River Gomti.', 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=800&q=80', '+91 522 6711000', 15),
        (dest_map['Lucknow'], 'Hyatt Regency Lucknow', 'Vibhuti Khand, Lucknow', 4.7, 5400.0, 'Regency King Room, Regency Suite', 'Rooftop Bar, Pool, 24/7 Dining, Fitness Center', 'Modern luxury hotel near major corporate and tourist hubs.', 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80', '+91 522 4261234', 22),
        (dest_map['Lucknow'], 'Lebua Lucknow - Heritage Hotel', 'Mall Avenue, Lucknow', 4.8, 6500.0, 'Executive Heritage, Art Deco Suite', 'Italian Bistro, Open Courtyard, Heritage Architecture', 'Boutique heritage hotel built in 1930s Art Deco style.', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80', '+91 522 2238333', 10),

        (dest_map['Jaipur'], 'Rambagh Palace Jaipur', 'Bhawani Singh Road, Jaipur', 4.9, 14500.0, 'Grand Royal Suite, Palace Room', 'Royal Butler, Indoor Pool, Spa, Polo Bar, Peacock Gardens', 'Former residence of the Maharaja of Jaipur.', 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80', '+91 141 2385700', 8),
        (dest_map['Jaipur'], 'ITC Rajputana', 'Palace Road, Jaipur', 4.8, 6900.0, 'Rajputana Chamber, Executive Club', 'Outdoor Pool, Royal Dining, Spa, Free High-Speed WiFi', 'Luxury hotel inspired by traditional Rajasthani Haveli design.', 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80', '+91 141 5100100', 25),
        (dest_map['Jaipur'], 'Shahpura House Heritage Hotel', 'Devi Marg, Bani Park, Jaipur', 4.6, 3800.0, 'Royal Deluxe, Suite Room', 'Rooftop Restaurant, Swimming Pool, Folk Dance Show', 'Authentic heritage haveli offering royal hospitality.', 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=800&q=80', '+91 141 2202293', 14),

        (dest_map['Goa'], 'Taj Exotica Resort & Spa', 'Benaulim Beach, South Goa', 4.9, 11200.0, 'Sea View Villa, Garden Villa', 'Private Beach, Golf Course, Outdoor Pools, Seafood Grill', 'Mediterranean-style 5-star resort located directly on Benaulim Beach.', 'https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80', '+91 832 6683333', 10),
        (dest_map['Goa'], 'W Goa Resort', 'Vagator Beach, North Goa', 4.8, 9800.0, 'Fabulous Room, Villa with Private Pool', 'Rock Pool Beach Bar, Spa, DJ Lounge, Water Sports', 'Trendy luxury resort overlooking scenic Vagator cliff.', 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80', '+91 832 6718888', 16),
        (dest_map['Goa'], 'Lemon Tree Amarante Beach Resort', 'Candolim, North Goa', 4.5, 4200.0, 'Superior Room, Heritage Studio', 'Swimming Pool, Gym, Citrus Cafe, Close to Beach', 'Charming Portuguese-style resort 200m from Candolim Beach.', 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80', '+91 832 3988188', 30),

        (dest_map['Agra'], 'The Oberoi Amarvilas', 'Taj East Gate Road, Agra', 4.9, 16800.0, 'Premier Taj View Room, Luxury Suite', 'Uninterrupted Taj Mahal View, Private Balcony, Spa, Butler', 'Every room offers direct uninterrupted views of the Taj Mahal.', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80', '+91 562 2231515', 6),
        (dest_map['Agra'], 'Courtyard by Marriott Agra', 'Fatehabad Road, Agra', 4.6, 4500.0, 'Deluxe Room, Executive Suite', 'Outdoor Pool, 24-hr Fitness Center, Multiple Restaurants', 'Contemporary 5-star hotel near Agra Fort.', 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80', '+91 562 6627777', 24),

        (dest_map['Shimla'], 'Wildflower Hall, An Oberoi Resort', 'Chharabra, Shimla', 4.9, 13500.0, 'Deluxe Garden View, Premier Mountain View', 'Heated Open-Air Whirlpool, Himalayan Views, Nature Walks', 'Luxury mountain resort situated at 8,250 feet amidst pine forests.', 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=800&q=80', '+91 177 2648585', 9),
        (dest_map['Shimla'], 'The Cecil - Oberoi Heritage Resort', 'Chaura Maidan, Shimla', 4.8, 8900.0, 'Luxury Suite, Mountain View Deluxe', 'Indoor Heated Pool, Heritage Lounge, Cedar Garden', '140-year-old grand heritage hotel on Shimla hill.', 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80', '+91 177 2804848', 12)
    ]

    cur.executemany('''
    INSERT INTO hotels (destination_id, name, location, rating, price_per_night, room_types, amenities, description, image_url, contact, available_rooms)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', hotels_data)

    conn.commit()
    conn.close()
    print("Database initialization and seed complete!")

if __name__ == '__main__':
    init_db()
