import os
import random
import string
import hashlib
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, session
from database import query_db, execute_db, execute_many_db, get_db

app = Flask(__name__)
app.secret_key = 'railexpress_secret_key_super_secure_tournament_2026'

def calculate_age(dob_str):
    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return 0

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# ----------------- AUTH ENDPOINTS -----------------

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.json or {}
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    dob = data.get('dob', '')
    phone = data.get('phone', '').strip()

    if not full_name or not email or not password or not dob:
        return jsonify({'error': 'Full name, email, password, and date of birth are required.'}), 400

    # Strict Age Restriction Validation (Backend Enforced)
    user_age = calculate_age(dob)
    if user_age < 18:
        return jsonify({
            'error': f'Registration rejected. Platform is strictly for users 18 years or older. Your calculated age is {user_age} years.'
        }), 400

    existing = query_db('SELECT id FROM users WHERE email = ?', (email,), one=True)
    if existing:
        return jsonify({'error': 'An account with this email already exists.'}), 400

    pw_hash = hash_password(password)
    user_id = execute_db('''
    INSERT INTO users (full_name, email, password_hash, dob, phone)
    VALUES (?, ?, ?, ?, ?)
    ''', (full_name, email, pw_hash, dob, phone))

    session['user_id'] = user_id
    session['user_name'] = full_name
    session['user_email'] = email

    return jsonify({
        'message': 'Account created successfully!',
        'user': {'id': user_id, 'full_name': full_name, 'email': email, 'dob': dob}
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    pw_hash = hash_password(password)
    user = query_db('SELECT * FROM users WHERE email = ? AND password_hash = ?', (email, pw_hash), one=True)

    if not user:
        return jsonify({'error': 'Invalid email or password.'}), 401

    # Check age upon login just in case
    user_age = calculate_age(user['dob'])
    if user_age < 18:
        return jsonify({'error': 'Account access denied. Must be 18 years or older.'}), 403

    session['user_id'] = user['id']
    session['user_name'] = user['full_name']
    session['user_email'] = user['email']

    return jsonify({
        'message': 'Logged in successfully!',
        'user': {'id': user['id'], 'full_name': user['full_name'], 'email': user['email'], 'dob': user['dob']}
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully.'})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 200

    user = query_db('SELECT id, full_name, email, dob, phone FROM users WHERE id = ?', (user_id,), one=True)
    if not user:
        session.clear()
        return jsonify({'authenticated': False}), 200

    return jsonify({
        'authenticated': True,
        'user': dict(user)
    })

# ----------------- STATIONS & TRAIN SEARCH -----------------

@app.route('/api/stations', methods=['GET'])
def get_stations():
    stations = query_db('SELECT * FROM stations ORDER BY city ASC, name ASC')
    return jsonify([dict(s) for s in stations])

@app.route('/api/trains/search', methods=['GET'])
def search_trains():
    from_stn = request.args.get('from', '').strip()
    to_stn = request.args.get('to', '').strip()
    journey_date = request.args.get('date', '').strip()
    passengers = int(request.args.get('passengers', 1))
    class_code = request.args.get('class_code', 'ALL')
    sort_by = request.args.get('sort_by', 'cheapest') # cheapest, fastest, earliest, availability

    if not journey_date:
        journey_date = date.today().strftime('%Y-%m-%d')

    # Base query finding trains stopping at both From and To where origin_seq < dest_seq
    sql = '''
    SELECT 
        t.id, t.train_number, t.train_name, t.train_type, t.operating_days, 
        t.departure_time, t.arrival_time, t.duration, t.base_fare, t.amenities,
        s1.departure_time as origin_dep_time, s1.stop_seq as origin_seq, s1.distance_km as origin_dist,
        s2.arrival_time as dest_arr_time, s2.stop_seq as dest_seq, s2.distance_km as dest_dist,
        st1.name as origin_name, st1.city as origin_city, st1.code as origin_code,
        st2.name as dest_name, st2.city as dest_city, st2.code as dest_code
    FROM trains t
    JOIN train_stops s1 ON t.id = s1.train_id
    JOIN train_stops s2 ON t.id = s2.train_id
    JOIN stations st1 ON s1.station_id = st1.id
    JOIN stations st2 ON s2.station_id = st2.id
    WHERE (st1.code = ? OR st1.id = ? OR st1.city LIKE ?)
      AND (st2.code = ? OR st2.id = ? OR st2.city LIKE ?)
      AND s1.stop_seq < s2.stop_seq
    '''
    params = (from_stn, from_stn, f'%{from_stn}%', to_stn, to_stn, f'%{to_stn}%')
    rows = query_db(sql, params)

    # If no specific search criteria provided, return popular trains
    if not rows and not from_stn and not to_stn:
        rows = query_db('''
        SELECT 
            t.id, t.train_number, t.train_name, t.train_type, t.operating_days, 
            t.departure_time, t.arrival_time, t.duration, t.base_fare, t.amenities,
            t.departure_time as origin_dep_time, 1 as origin_seq, 0 as origin_dist,
            t.arrival_time as dest_arr_time, 4 as dest_seq, 780 as dest_dist,
            st1.name as origin_name, st1.city as origin_city, st1.code as origin_code,
            st2.name as dest_name, st2.city as dest_city, st2.code as dest_code
        FROM trains t
        JOIN stations st1 ON t.origin_station_id = st1.id
        JOIN stations st2 ON t.dest_station_id = st2.id
        LIMIT 15
        ''')

    train_results = []
    for r in rows:
        t_dict = dict(r)
        tid = t_dict['id']

        # Get available classes and prices
        classes = query_db('SELECT * FROM train_classes WHERE train_id = ?', (tid,))
        class_list = []
        
        # Calculate seat availability from DB
        for c in classes:
            ccode = c['class_code']
            cname = c['class_name']
            total_seats = c['total_seats']
            multiplier = c['price_multiplier']
            calculated_fare = round(t_dict['base_fare'] * multiplier, 2)

            # Count booked seats for this date
            booked_count = query_db('''
            SELECT COUNT(*) as count FROM seat_bookings 
            WHERE train_id = ? AND journey_date = ? AND class_code = ?
            ''', (tid, journey_date, ccode), one=True)['count']

            available_seats = max(0, total_seats - booked_count)

            class_list.append({
                'class_code': ccode,
                'class_name': cname,
                'total_seats': total_seats,
                'available_seats': available_seats,
                'fare': calculated_fare
            })

        # Filter by class_code if specified
        if class_code != 'ALL':
            class_list = [cl for cl in class_list if cl['class_code'] == class_code]
            if not class_list:
                continue

        t_dict['classes'] = class_list
        t_dict['amenities_list'] = [a.strip() for a in t_dict['amenities'].split(',')]
        
        # Calculate journey duration string
        t_dict['calculated_fare'] = class_list[0]['fare'] if class_list else t_dict['base_fare']
        t_dict['total_available_seats'] = sum(cl['available_seats'] for cl in class_list)

        train_results.append(t_dict)

    # Sorting
    if sort_by == 'cheapest':
        train_results.sort(key=lambda x: x['calculated_fare'])
    elif sort_by == 'fastest':
        train_results.sort(key=lambda x: x['duration'])
    elif sort_by == 'earliest':
        train_results.sort(key=lambda x: x['origin_dep_time'])
    elif sort_by == 'availability':
        train_results.sort(key=lambda x: x['total_available_seats'], reverse=True)

    return jsonify(train_results)

# ----------------- TRAIN DETAILS & SCHEDULE TIMELINE -----------------

@app.route('/api/trains/<int:train_id>', methods=['GET'])
def get_train_details(train_id):
    train = query_db('''
    SELECT t.*, st1.name as origin_name, st1.city as origin_city, st1.code as origin_code,
           st2.name as dest_name, st2.city as dest_city, st2.code as dest_code
    FROM trains t
    JOIN stations st1 ON t.origin_station_id = st1.id
    JOIN stations st2 ON t.dest_station_id = st2.id
    WHERE t.id = ?
    ''', (train_id,), one=True)

    if not train:
        return jsonify({'error': 'Train not found.'}), 404

    t_dict = dict(train)

    # Fetch intermediate stops timeline from train_stops database
    stops = query_db('''
    SELECT ts.*, st.name as station_name, st.code as station_code, st.city as station_city
    FROM train_stops ts
    JOIN stations st ON ts.station_id = st.id
    WHERE ts.train_id = ?
    ORDER BY ts.stop_seq ASC
    ''', (train_id,))

    # Fetch classes
    classes = query_db('SELECT * FROM train_classes WHERE train_id = ?', (train_id,))
    class_list = []
    for c in classes:
        cd = dict(c)
        cd['fare'] = round(t_dict['base_fare'] * cd['price_multiplier'], 2)
        class_list.append(cd)

    t_dict['schedule_timeline'] = [dict(s) for s in stops]
    t_dict['classes'] = class_list
    t_dict['amenities_list'] = [a.strip() for a in t_dict['amenities'].split(',')]

    return jsonify(t_dict)

# ----------------- SEAT SELECTION SYSTEM -----------------

@app.route('/api/seats', methods=['GET'])
def get_seats():
    train_id = request.args.get('train_id', type=int)
    class_code = request.args.get('class_code', '3A')
    journey_date = request.args.get('journey_date', date.today().strftime('%Y-%m-%d'))

    if not train_id:
        return jsonify({'error': 'train_id is required.'}), 400

    # Get seat template for this train and class
    seats_template = query_db('''
    SELECT * FROM seats 
    WHERE train_id = ? AND class_code = ?
    ORDER BY coach_number ASC, seat_number ASC
    ''', (train_id, class_code))

    # Get booked seat numbers for this train, date, and class from DB
    booked_rows = query_db('''
    SELECT seat_number FROM seat_bookings 
    WHERE train_id = ? AND journey_date = ? AND class_code = ?
    ''', (train_id, journey_date, class_code))

    booked_seats_set = {str(b['seat_number']) for b in booked_rows}

    seat_list = []
    for s in seats_template:
        s_dict = dict(s)
        s_num_str = str(s_dict['seat_number'])
        s_dict['status'] = 'occupied' if s_num_str in booked_seats_set else 'available'
        seat_list.append(s_dict)

    return jsonify({
        'train_id': train_id,
        'class_code': class_code,
        'journey_date': journey_date,
        'seats': seat_list
    })

# ----------------- BOOKING SYSTEM & PNR -----------------

@app.route('/api/bookings/create', methods=['POST'])
def create_booking():
    data = request.json or {}
    train_id = data.get('train_id')
    journey_date = data.get('journey_date')
    class_code = data.get('class_code')
    passengers = data.get('passengers', [])

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required. Please log in to complete your train booking.'}), 401

    if not train_id or not journey_date or not class_code or not passengers:
        return jsonify({'error': 'Missing train details, journey date, class, or passenger details.'}), 400

    train = query_db('SELECT * FROM trains WHERE id = ?', (train_id,), one=True)
    if not train:
        return jsonify({'error': 'Invalid train selected.'}), 404

    class_info = query_db('SELECT price_multiplier FROM train_classes WHERE train_id = ? AND class_code = ?',
                          (train_id, class_code), one=True)
    multiplier = class_info['price_multiplier'] if class_info else 1.0
    unit_fare = round(train['base_fare'] * multiplier, 2)
    total_fare = round(unit_fare * len(passengers), 2)

    conn = get_db()
    cur = conn.cursor()

    try:
        # Atomic Seat Availability Check to Prevent Double Bookings
        requested_seats = [str(p.get('seat_number')) for p in passengers if p.get('seat_number')]
        if requested_seats:
            placeholders = ','.join(['?'] * len(requested_seats))
            query = f'''
            SELECT seat_number FROM seat_bookings 
            WHERE train_id = ? AND journey_date = ? AND class_code = ? AND seat_number IN ({placeholders})
            '''
            params = [train_id, journey_date, class_code] + requested_seats
            cur.execute(query, params)
            conflicts = cur.fetchall()

            if conflicts:
                conflicting_seats = [c['seat_number'] for c in conflicts]
                conn.close()
                return jsonify({
                    'error': f'Seat conflict detected! The following seat(s) are already booked for {journey_date}: {", ".join(conflicting_seats)}. Please select different seats.'
                }), 409

        # Generate unique 10-digit PNR
        random_digits = ''.join(random.choices(string.digits, k=7))
        pnr = f"PNR-{random_digits}"

        # Insert Booking
        cur.execute('''
        INSERT INTO bookings (pnr, user_id, train_id, journey_date, class_code, total_fare, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (pnr, user_id, train_id, journey_date, class_code, total_fare, 'CONFIRMED'))
        booking_id = cur.lastrowid

        # Insert Passengers & Lock Seats in Database
        for p in passengers:
            fname = p.get('full_name', '').strip()
            age = int(p.get('age', 25))
            gender = p.get('gender', 'Other')
            seat_num = str(p.get('seat_number', 'Unassigned'))

            cur.execute('''
            INSERT INTO booking_passengers (booking_id, full_name, age, gender, seat_number)
            VALUES (?, ?, ?, ?, ?)
            ''', (booking_id, fname, age, gender, seat_num))

            cur.execute('''
            INSERT INTO seat_bookings (train_id, journey_date, class_code, seat_number, booking_id)
            VALUES (?, ?, ?, ?, ?)
            ''', (train_id, journey_date, class_code, seat_num, booking_id))

        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Booking confirmed successfully!',
            'pnr': pnr,
            'booking_id': booking_id,
            'total_fare': total_fare,
            'status': 'CONFIRMED'
        })

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Failed to process booking: {str(e)}'}), 500

# ----------------- MY BOOKINGS & TICKET CANCEL -----------------

@app.route('/api/bookings/my-bookings', methods=['GET'])
def get_my_bookings():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required.'}), 401

    bookings = query_db('''
    SELECT b.*, t.train_number, t.train_name, t.departure_time, t.arrival_time, t.duration,
           st1.name as origin_name, st1.city as origin_city,
           st2.name as dest_name, st2.city as dest_city
    FROM bookings b
    JOIN trains t ON b.train_id = t.id
    JOIN stations st1 ON t.origin_station_id = st1.id
    JOIN stations st2 ON t.dest_station_id = st2.id
    WHERE b.user_id = ?
    ORDER BY b.created_at DESC
    ''', (user_id,))

    booking_list = []
    for b in bookings:
        b_dict = dict(b)
        passengers = query_db('SELECT * FROM booking_passengers WHERE booking_id = ?', (b_dict['id'],))
        b_dict['passengers'] = [dict(p) for p in passengers]
        booking_list.append(b_dict)

    return jsonify(booking_list)

@app.route('/api/bookings/cancel', methods=['POST'])
def cancel_booking():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required.'}), 401

    data = request.json or {}
    booking_id = data.get('booking_id')

    if not booking_id:
        return jsonify({'error': 'booking_id is required.'}), 400

    booking = query_db('SELECT * FROM bookings WHERE id = ? AND user_id = ?', (booking_id, user_id), one=True)
    if not booking:
        return jsonify({'error': 'Booking not found or access denied.'}), 404

    if booking['status'] == 'CANCELLED':
        return jsonify({'error': 'Booking is already cancelled.'}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE bookings SET status = 'CANCELLED' WHERE id = ?", (booking_id,))
    # Free up seat locks in database immediately
    cur.execute("DELETE FROM seat_bookings WHERE booking_id = ?", (booking_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Booking cancelled successfully. Seat availability has been updated.'})

# ----------------- TOURIST & TRAVEL SECTION -----------------

@app.route('/api/tourist/destinations', methods=['GET'])
def get_destinations():
    destinations = query_db('SELECT * FROM destinations ORDER BY name ASC')
    dest_list = []
    for d in destinations:
        dd = dict(d)
        attractions = query_db('SELECT * FROM attractions WHERE destination_id = ?', (dd['id'],))
        dd['attractions'] = [dict(a) for a in attractions]
        dest_list.append(dd)
    return jsonify(dest_list)

@app.route('/api/tourist/destinations/<int:dest_id>', methods=['GET'])
def get_destination_detail(dest_id):
    dest = query_db('SELECT * FROM destinations WHERE id = ?', (dest_id,), one=True)
    if not dest:
        return jsonify({'error': 'Destination not found.'}), 404

    dd = dict(dest)
    dd['attractions'] = [dict(a) for a in query_db('SELECT * FROM attractions WHERE destination_id = ?', (dest_id,))]
    dd['itineraries'] = [dict(i) for i in query_db('SELECT * FROM itineraries WHERE destination_id = ?', (dest_id,))]
    dd['hotels'] = [dict(h) for h in query_db('SELECT * FROM hotels WHERE destination_id = ?', (dest_id,))]

    return jsonify(dd)

# ----------------- HOTELS SECTION -----------------

@app.route('/api/tourist/hotels', methods=['GET'])
def get_hotels():
    dest_id = request.args.get('destination_id', type=int)
    city = request.args.get('city', '').strip()

    if dest_id:
        hotels = query_db('SELECT h.*, d.name as destination_name FROM hotels h JOIN destinations d ON h.destination_id = d.id WHERE h.destination_id = ?', (dest_id,))
    elif city:
        hotels = query_db('SELECT h.*, d.name as destination_name FROM hotels h JOIN destinations d ON h.destination_id = d.id WHERE d.name LIKE ? OR h.location LIKE ?', (f'%{city}%', f'%{city}%'))
    else:
        hotels = query_db('SELECT h.*, d.name as destination_name FROM hotels h JOIN destinations d ON h.destination_id = d.id ORDER BY h.rating DESC')

    hotel_list = []
    for h in hotels:
        hd = dict(h)
        hd['amenities_list'] = [a.strip() for a in hd['amenities'].split(',')]
        hd['room_types_list'] = [r.strip() for r in hd['room_types'].split(',')]
        hotel_list.append(hd)

    return jsonify(hotel_list)

# ----------------- MAIN HTML ROUTE -----------------

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print("Starting RailExpress Premier Server on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=True)
