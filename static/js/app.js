// RailExpress Premier SPA Core Engine

let currentUser = null;
let currentSearchData = [];
let selectedTrain = null;
let selectedClass = '3A';
let selectedSeats = [];
let currentJourneyDate = new Date().toISOString().split('T')[0];

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupDatePickers();
    await checkAuth();
    await loadStations();
    await executeSearch();
    await loadDestinations();
    await loadHotels();
}

function setupDatePickers() {
    const today = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById('search-date');
    if (dateInput) {
        dateInput.value = today;
        dateInput.min = today;
    }
}

// ----------------- AUTHENTICATION & AGE RESTRICTION -----------------

async function checkAuth() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (data.authenticated) {
            currentUser = data.user;
            renderAuthHeader(true);
        } else {
            currentUser = null;
            renderAuthHeader(false);
        }
    } catch (e) {
        console.error('Auth check error:', e);
    }
}

function renderAuthHeader(isLoggedIn) {
    const container = document.getElementById('auth-nav-container');
    if (!container) return;

    if (isLoggedIn && currentUser) {
        container.innerHTML = `
            <div style="display:flex; align-items:center; gap:1rem;">
                <span style="font-weight:600; color:var(--accent);">👤 ${currentUser.full_name}</span>
                <button class="btn btn-outline btn-sm" onclick="openMyBookings()">🎟 My Bookings</button>
                <button class="btn btn-outline btn-sm" onclick="handleLogout()">Log Out</button>
            </div>
        `;
    } else {
        container.innerHTML = `
            <button class="btn btn-outline btn-sm" onclick="openModal('login-modal')">Log In</button>
            <button class="btn btn-accent btn-sm" onclick="openModal('signup-modal')">Sign Up</button>
        `;
    }
}

async function handleSignup(e) {
    e.preventDefault();
    const errorBox = document.getElementById('signup-error');
    errorBox.style.display = 'none';

    const fullName = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const dob = document.getElementById('signup-dob').value;
    const phone = document.getElementById('signup-phone').value;

    try {
        const res = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: fullName, email, password, dob, phone })
        });
        const data = await res.json();

        if (!res.ok) {
            errorBox.innerText = data.error || 'Signup failed.';
            errorBox.style.display = 'block';
            return;
        }

        closeModal('signup-modal');
        await checkAuth();
        alert('🎉 Welcome to RailExpress! Account created successfully.');
    } catch (err) {
        errorBox.innerText = 'Server error during signup.';
        errorBox.style.display = 'block';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const errorBox = document.getElementById('login-error');
    errorBox.style.display = 'none';

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (!res.ok) {
            errorBox.innerText = data.error || 'Login failed.';
            errorBox.style.display = 'block';
            return;
        }

        closeModal('login-modal');
        await checkAuth();
    } catch (err) {
        errorBox.innerText = 'Server connection error.';
        errorBox.style.display = 'block';
    }
}

async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    await checkAuth();
    alert('You have logged out.');
}

// ----------------- STATIONS & SEARCH -----------------

async function loadStations() {
    try {
        const res = await fetch('/api/stations');
        const stations = await res.json();

        const fromSelect = document.getElementById('search-from');
        const toSelect = document.getElementById('search-to');

        if (!fromSelect || !toSelect) return;

        let optionsHtml = '<option value="">All Origin Stations</option>';
        let optionsToHtml = '<option value="">All Destination Stations</option>';

        stations.forEach(s => {
            optionsHtml += `<option value="${s.code}">${s.city} (${s.code}) - ${s.name}</option>`;
            optionsToHtml += `<option value="${s.code}">${s.city} (${s.code}) - ${s.name}</option>`;
        });

        fromSelect.innerHTML = optionsHtml;
        toSelect.innerHTML = optionsToHtml;

        // Default selections for rich search presentation
        fromSelect.value = 'NDLS';
        toSelect.value = 'BSB';
    } catch (e) {
        console.error('Failed loading stations:', e);
    }
}

async function executeSearch() {
    const fromVal = document.getElementById('search-from')?.value || '';
    const toVal = document.getElementById('search-to')?.value || '';
    const dateVal = document.getElementById('search-date')?.value || currentJourneyDate;
    const passengersVal = document.getElementById('search-passengers')?.value || 1;
    const classVal = document.getElementById('search-class')?.value || 'ALL';
    const sortBy = document.getElementById('sort-by')?.value || 'cheapest';

    currentJourneyDate = dateVal;

    const url = `/api/trains/search?from=${encodeURIComponent(fromVal)}&to=${encodeURIComponent(toVal)}&date=${dateVal}&passengers=${passengersVal}&class_code=${classVal}&sort_by=${sortBy}`;
    
    const resultsContainer = document.getElementById('train-results-container');
    resultsContainer.innerHTML = '<div style="text-align:center; padding:3rem; color:var(--accent);">🚆 Querying Railway Network Database...</div>';

    try {
        const res = await fetch(url);
        currentSearchData = await res.json();
        renderTrainResults(currentSearchData);
    } catch (e) {
        resultsContainer.innerHTML = '<div style="text-align:center; color:var(--danger);">Error searching train database.</div>';
    }
}

function renderTrainResults(trains) {
    const container = document.getElementById('train-results-container');
    if (!container) return;

    if (!trains || trains.length === 0) {
        container.innerHTML = `
            <div style="background:var(--bg-card); border:1px solid var(--border-glass); padding:3rem; text-align:center; border-radius:var(--radius-md);">
                <h3>No Direct Trains Found</h3>
                <p style="color:var(--text-muted); margin-top:0.5rem;">Try selecting different origin/destination stations or dates.</p>
            </div>
        `;
        return;
    }

    let html = '';
    trains.forEach(t => {
        const classesHtml = t.classes.map(c => `
            <button class="btn btn-outline btn-sm ${c.available_seats === 0 ? 'disabled' : ''}" 
                    onclick="openSeatSelection(${t.id}, '${c.class_code}', ${c.fare})">
                ${c.class_code} - ₹${c.fare} 
                <span class="seats-badge ${c.available_seats > 5 ? 'seats-avail' : ''}">${c.available_seats} Seats</span>
            </button>
        `).join(' ');

        html += `
            <div class="train-card">
                <div>
                    <div class="train-info-header">
                        <span class="train-number-badge">#${t.train_number}</span>
                        <span class="train-type-pill">${t.train_type}</span>
                    </div>
                    <div class="train-name">${t.train_name}</div>
                    <div style="font-size:0.85rem; color:var(--text-muted); margin-top:0.3rem;">
                        📅 Runs: <strong style="color:#fff;">${t.operating_days}</strong>
                    </div>
                    <div style="margin-top:0.75rem;">
                        <button class="btn btn-outline btn-sm" onclick="openTrainScheduleModal(${t.id})">
                            🕒 View Full Schedule & Stops
                        </button>
                    </div>
                </div>

                <div>
                    <div class="route-timeline-box">
                        <div class="time-node">
                            <div class="time-val">${t.departure_time}</div>
                            <div class="stn-code">${t.origin_code}</div>
                            <div class="stn-city">${t.origin_city}</div>
                        </div>
                        <div class="duration-line">
                            <div class="duration-label">⏱ ${t.duration}</div>
                            <div class="line-graphic"></div>
                        </div>
                        <div class="time-node">
                            <div class="time-val">${t.arrival_time}</div>
                            <div class="stn-code">${t.dest_code}</div>
                            <div class="stn-city">${t.dest_city}</div>
                        </div>
                    </div>
                </div>

                <div class="class-fare-grid">
                    <div style="text-align:right;">
                        <span class="fare-unit">Starting from</span>
                        <div class="fare-amount">₹${t.calculated_fare}</div>
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:0.4rem; justify-content:flex-end;">
                        ${classesHtml}
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ----------------- SCHEDULE TIMELINE MODAL -----------------

async function openTrainScheduleModal(trainId) {
    try {
        const res = await fetch(`/api/trains/${trainId}`);
        const t = await res.json();

        document.getElementById('schedule-modal-title').innerText = `${t.train_name} (#${t.train_number}) Schedule`;
        
        let timelineHtml = `
            <div style="display:flex; justify-content:space-between; background:rgba(11, 19, 43, 0.8); padding:1rem; border-radius:var(--radius-sm); margin-bottom:1rem;">
                <div><strong>Type:</strong> ${t.train_type}</div>
                <div><strong>Runs On:</strong> ${t.operating_days}</div>
                <div><strong>Base Fare:</strong> ₹${t.base_fare}</div>
            </div>
            <h4>Intermediate Stations & Stop Timings</h4>
            <div class="timeline-list">
        `;

        t.schedule_timeline.forEach((stop, index) => {
            timelineHtml += `
                <div class="timeline-item">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <strong style="font-size:1.1rem; color:#fff;">${stop.stop_seq}. ${stop.station_name} (${stop.station_code})</strong>
                            <div style="font-size:0.85rem; color:var(--text-muted);">${stop.station_city} • ${stop.distance_km} km from origin</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="color:var(--accent); font-weight:700;">Arr: ${stop.arrival_time || 'Start'} | Dep: ${stop.departure_time || 'Terminus'}</div>
                            <div style="font-size:0.75rem; color:var(--text-muted);">Day ${stop.day_number}</div>
                        </div>
                    </div>
                </div>
            `;
        });

        timelineHtml += '</div>';

        document.getElementById('schedule-modal-content').innerHTML = timelineHtml;
        openModal('schedule-modal');
    } catch (e) {
        alert('Could not load schedule timeline.');
    }
}

// ----------------- SEAT SELECTION & MATRIX -----------------

async function openSeatSelection(trainId, classCode, fare) {
    if (!currentUser) {
        openModal('login-modal');
        alert('Please log in or sign up to select seats and book tickets.');
        return;
    }

    selectedTrain = currentSearchData.find(t => t.id === trainId);
    selectedClass = classCode;
    selectedSeats = [];

    document.getElementById('seat-train-info').innerText = `${selectedTrain.train_name} (#${selectedTrain.train_number}) — Class ${classCode} — ₹${fare}/seat`;
    
    await renderSeatGrid(trainId, classCode);
    openModal('seat-modal');
}

async function renderSeatGrid(trainId, classCode) {
    const grid = document.getElementById('coach-grid');
    grid.innerHTML = '<div style="grid-column:1/-1; text-align:center;">Loading seat layout...</div>';

    try {
        const res = await fetch(`/api/seats?train_id=${trainId}&class_code=${classCode}&journey_date=${currentJourneyDate}`);
        const data = await res.json();

        let html = '';
        data.seats.forEach(s => {
            const isOccupied = s.status === 'occupied';
            const isSelected = selectedSeats.includes(s.seat_number);
            let stateClass = isOccupied ? 'occupied' : (isSelected ? 'selected' : 'available');

            html += `
                <button class="seat-btn ${stateClass}" 
                        ${isOccupied ? 'disabled' : ''} 
                        onclick="toggleSeatSelection(${s.seat_number}, ${selectedTrain.calculated_fare})">
                    <span>${s.coach_number}-${s.seat_number}</span>
                    <span class="seat-type-sub">${s.seat_type}</span>
                </button>
            `;
        });

        grid.innerHTML = html;
        updateSelectedSeatsSummary();
    } catch (e) {
        grid.innerHTML = '<div style="grid-column:1/-1; color:var(--danger);">Error loading seats.</div>';
    }
}

function toggleSeatSelection(seatNum, fare) {
    const idx = selectedSeats.indexOf(seatNum);
    if (idx > -1) {
        selectedSeats.splice(idx, 1);
    } else {
        selectedSeats.push(seatNum);
    }
    renderSeatGrid(selectedTrain.id, selectedClass);
}

function updateSelectedSeatsSummary() {
    const summaryBox = document.getElementById('seat-summary-box');
    const passengerCount = parseInt(document.getElementById('search-passengers')?.value || 1);
    
    // Class multiplier fare
    const classObj = selectedTrain?.classes?.find(c => c.class_code === selectedClass);
    const unitFare = classObj ? classObj.fare : selectedTrain?.calculated_fare || 1000;
    const totalFare = unitFare * selectedSeats.length;

    summaryBox.innerHTML = `
        <div>Selected Seats: <strong>${selectedSeats.length > 0 ? selectedSeats.join(', ') : 'None'}</strong></div>
        <div style="font-size:1.3rem; font-weight:800; color:var(--accent);">Total: ₹${totalFare}</div>
    `;

    const proceedBtn = document.getElementById('proceed-checkout-btn');
    proceedBtn.disabled = selectedSeats.length === 0;
}

// ----------------- CHECKOUT & BOOKING -----------------

function proceedToCheckout() {
    closeModal('seat-modal');

    // Build passenger input fields
    const container = document.getElementById('passenger-inputs-container');
    let html = '';

    selectedSeats.forEach((seat, idx) => {
        html += `
            <div style="background:rgba(11, 19, 43, 0.6); padding:1rem; border-radius:var(--radius-sm); margin-bottom:1rem;">
                <h5>Passenger ${idx + 1} (Seat: ${selectedClass}1-${seat})</h5>
                <div style="display:grid; grid-template-columns: 2fr 1fr 1fr; gap:0.75rem; margin-top:0.5rem;">
                    <input type="text" class="form-control passenger-name" placeholder="Full Name" value="${idx === 0 ? currentUser.full_name : ''}" required>
                    <input type="number" class="form-control passenger-age" placeholder="Age" min="1" max="110" value="28" required>
                    <select class="form-select passenger-gender">
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                    </select>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;

    const classObj = selectedTrain.classes.find(c => c.class_code === selectedClass);
    const baseTotal = classObj.fare * selectedSeats.length;
    const gst = Math.round(baseTotal * 0.05);
    const grandTotal = baseTotal + gst;

    document.getElementById('checkout-summary-breakdown').innerHTML = `
        <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
            <span>Train:</span> <strong>${selectedTrain.train_name} (#${selectedTrain.train_number})</strong>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
            <span>Route & Date:</span> <strong>${selectedTrain.origin_code} ➔ ${selectedTrain.dest_code} (${currentJourneyDate})</strong>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;">
            <span>Class & Seats:</span> <strong>${selectedClass} (${selectedSeats.join(', ')})</strong>
        </div>
        <hr style="border-color:var(--border-glass); margin:0.8rem 0;">
        <div style="display:flex; justify-content:space-between;">
            <span>Base Fare (${selectedSeats.length} Pax):</span> <span>₹${baseTotal}</span>
        </div>
        <div style="display:flex; justify-content:space-between;">
            <span>Taxes & Fees (GST 5%):</span> <span>₹${gst}</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:1.3rem; font-weight:800; color:var(--accent); margin-top:0.5rem;">
            <span>Total Payable:</span> <span>₹${grandTotal}</span>
        </div>
    `;

    openModal('checkout-modal');
}

async function confirmBookingPayment(e) {
    e.preventDefault();

    const passengerNames = document.querySelectorAll('.passenger-name');
    const passengerAges = document.querySelectorAll('.passenger-age');
    const passengerGenders = document.querySelectorAll('.passenger-gender');

    const passengersList = [];
    selectedSeats.forEach((seat, i) => {
        passengersList.push({
            full_name: passengerNames[i].value,
            age: parseInt(passengerAges[i].value),
            gender: passengerGenders[i].value,
            seat_number: seat
        });
    });

    try {
        const res = await fetch('/api/bookings/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                train_id: selectedTrain.id,
                journey_date: currentJourneyDate,
                class_code: selectedClass,
                passengers: passengersList
            })
        });

        const data = await res.json();

        if (!res.ok) {
            alert('❌ Booking Error: ' + (data.error || 'Failed to book'));
            return;
        }

        closeModal('checkout-modal');
        alert(`🎉 Booking Confirmed! Generated PNR: ${data.pnr}`);
        openMyBookings();
    } catch (e) {
        alert('Server error confirming booking.');
    }
}

// ----------------- MY BOOKINGS & TICKET VIEWER -----------------

async function openMyBookings() {
    if (!currentUser) {
        openModal('login-modal');
        return;
    }

    try {
        const res = await fetch('/api/bookings/my-bookings');
        const bookings = await res.json();

        const container = document.getElementById('my-bookings-list');
        if (!container) return;

        if (!bookings || bookings.length === 0) {
            container.innerHTML = '<div style="text-align:center; padding:2rem;">No bookings found. Search trains to book your journey!</div>';
        } else {
            let html = '';
            bookings.forEach(b => {
                const paxNames = b.passengers.map(p => `${p.full_name} (${p.age}y, ${p.gender}) - Seat ${p.seat_number}`).join('<br>');
                const isCancelled = b.status === 'CANCELLED';

                html += `
                    <div style="background:var(--bg-card); border:1px solid var(--border-glass); border-radius:var(--radius-md); padding:1.5rem; margin-bottom:1.5rem; ${isCancelled ? 'opacity:0.6;' : ''}">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                            <div class="pnr-tag" style="font-size:1.2rem;">${b.pnr}</div>
                            <span class="seats-badge ${isCancelled ? 'dot-occupied' : 'seats-avail'}" style="font-size:0.9rem;">
                                ${b.status}
                            </span>
                        </div>
                        <div style="display:grid; grid-template-columns: 2fr 1fr; gap:1rem;">
                            <div>
                                <h4 style="color:#fff;">${b.train_name} (#${b.train_number})</h4>
                                <div>Route: <strong>${b.origin_city} ➔ ${b.dest_city}</strong></div>
                                <div>Date: <strong>${b.journey_date}</strong> | Dep: ${b.departure_time}</div>
                                <div style="margin-top:0.75rem; font-size:0.9rem;">
                                    <strong>Passengers:</strong><br>${paxNames}
                                </div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:1.4rem; font-weight:800; color:var(--accent);">₹${b.total_fare}</div>
                                ${!isCancelled ? `
                                    <button class="btn btn-outline btn-sm" style="margin-top:1rem; border-color:var(--danger); color:var(--danger);" onclick="cancelBooking(${b.id})">
                                        ❌ Cancel Ticket
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        openModal('my-bookings-modal');
    } catch (e) {
        alert('Could not fetch bookings.');
    }
}

async function cancelBooking(bookingId) {
    if (!confirm('Are you sure you want to cancel this booking? Seats will be immediately released back to the database.')) return;

    try {
        const res = await fetch('/api/bookings/cancel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ booking_id: bookingId })
        });
        const data = await res.json();
        alert(data.message);
        openMyBookings();
    } catch (e) {
        alert('Error cancelling booking.');
    }
}

// ----------------- TOURIST & HOTELS SECTION -----------------

async function loadDestinations() {
    const container = document.getElementById('destinations-grid');
    if (!container) return;

    try {
        const res = await fetch('/api/tourist/destinations');
        const dests = await res.json();

        let html = '';
        dests.forEach(d => {
            html += `
                <div class="tourist-card">
                    <div class="card-img-wrapper">
                        <img src="${d.image_url}" class="card-img" alt="${d.name}">
                        <div class="card-badge">⏱ ${d.recommended_duration}</div>
                    </div>
                    <div class="card-content">
                        <div class="card-title">${d.name}, ${d.state}</div>
                        <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem;">${d.tagline}</p>
                        <div style="font-size:0.85rem; margin-bottom:1rem;">
                            <strong> Famous Food:</strong> ${d.famous_food}
                        </div>
                        <button class="btn btn-outline btn-sm" style="width:100%;" onclick="openDestinationDetails(${d.id})">
                            🗺 View Itineraries & Attractions
                        </button>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<div>Error loading destinations.</div>';
    }
}

async function openDestinationDetails(destId) {
    try {
        const res = await fetch(`/api/tourist/destinations/${destId}`);
        const d = await res.json();

        let html = `
            <h2>${d.name} (${d.state})</h2>
            <p style="color:var(--text-muted); margin-bottom:1rem;">${d.description}</p>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; background:rgba(11, 19, 43, 0.6); padding:1rem; border-radius:var(--radius-sm); margin-bottom:1.5rem;">
                <div><strong>Best Time to Visit:</strong> ${d.best_time}</div>
                <div><strong>Local Transport:</strong> ${d.local_transport}</div>
            </div>
            
            <h3>📍 Top Attractions</h3>
            <ul style="margin-bottom:1.5rem; padding-left:1.2rem;">
                ${d.attractions.map(a => `<li style="margin-bottom:0.4rem;"><strong>${a.name}</strong> (${a.category}): ${a.description}</li>`).join('')}
            </ul>

            <h3>🧳 Ready-Made Travel Itineraries</h3>
        `;

        d.itineraries.forEach(itin => {
            html += `
                <div style="background:var(--bg-main); border:1px solid var(--border-glass); padding:1.25rem; border-radius:var(--radius-sm); margin-top:1rem;">
                    <h4>${itin.title} (${itin.duration_days} Days)</h4>
                    <p style="font-size:0.9rem; color:var(--accent); margin-bottom:0.75rem;">${itin.overview}</p>
                    <div style="font-size:0.85rem; line-height:1.6;">
                        <div>${itin.day1}</div>
                        <div>${itin.day2}</div>
                        ${itin.day3 ? `<div>${itin.day3}</div>` : ''}
                        ${itin.day4 ? `<div>${itin.day4}</div>` : ''}
                    </div>
                </div>
            `;
        });

        document.getElementById('dest-detail-content').innerHTML = html;
        openModal('dest-detail-modal');
    } catch (e) {
        alert('Could not load destination details.');
    }
}

async function loadHotels() {
    const container = document.getElementById('hotels-grid');
    if (!container) return;

    try {
        const res = await fetch('/api/tourist/hotels');
        const hotels = await res.json();

        let html = '';
        hotels.forEach(h => {
            html += `
                <div class="hotel-card">
                    <div class="card-img-wrapper">
                        <img src="${h.image_url}" class="card-img" alt="${h.name}">
                        <div class="card-badge">★ ${h.rating}</div>
                    </div>
                    <div class="card-content">
                        <div class="card-title">${h.name}</div>
                        <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.5rem;">📍 ${h.location}</div>
                        <p style="font-size:0.85rem; margin-bottom:1rem;">${h.description}</p>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span style="font-size:1.3rem; font-weight:800; color:var(--accent);">₹${h.price_per_night}</span>
                                <span style="font-size:0.8rem; color:var(--text-muted);">/ night</span>
                            </div>
                            <button class="btn btn-primary btn-sm" onclick="alert('Hotel recommendations provided by RailExpress Partner Engine. Contact: ${h.contact}')">
                                🏨 View Deal
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<div>Error loading hotels.</div>';
    }
}

// ----------------- MODAL HELPERS -----------------

function openModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.add('show');
}

function closeModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.remove('show');
}
