import sqlite3
import os
import math
from datetime import datetime, timedelta

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'blood_donation.db')

# Blood groups compatibility matrix
# Key: Recipient blood group
# Value: List of compatible donor blood groups
COMPATIBILITY_MATRIX = {
    'A+': ['A+', 'A-', 'O+', 'O-'],
    'A-': ['A-', 'O-'],
    'B+': ['B+', 'B-', 'O+', 'O-'],
    'B-': ['B-', 'O-'],
    'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
    'AB-': ['A-', 'B-', 'AB-', 'O-'],
    'O+': ['O+', 'O-'],
    'O-': ['O-']
}

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create donors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            contact TEXT NOT NULL,
            email TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            last_donation_date TEXT,
            availability INTEGER DEFAULT 1 -- 1 for available, 0 for unavailable
        )
    ''')
    
    # Create requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            hospital_name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            units_needed INTEGER NOT NULL,
            urgency TEXT NOT NULL, -- 'Critical', 'High', 'Medium', 'Low'
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT DEFAULT 'Pending', -- 'Pending', 'Matched', 'Fulfilled', 'Cancelled'
            date_created TEXT NOT NULL
        )
    ''')
    
    # Create inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            blood_group TEXT PRIMARY KEY,
            units_available INTEGER DEFAULT 0,
            last_updated TEXT NOT NULL
        )
    ''')
    
    # Seed inventory if empty
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        now_str = datetime.now().isoformat()
        initial_stock = {
            'A+': 15, 'A-': 5, 'B+': 12, 'B-': 4,
            'AB+': 8, 'AB-': 2, 'O+': 20, 'O-': 6
        }
        for bg in blood_groups:
            cursor.execute(
                "INSERT INTO inventory (blood_group, units_available, last_updated) VALUES (?, ?, ?)",
                (bg, initial_stock[bg], now_str)
            )
            
    # Seed some dummy donors if empty
    cursor.execute("SELECT COUNT(*) FROM donors")
    if cursor.fetchone()[0] == 0:
        # Mock latitude and longitude around standard center (Mumbai, e.g. 19.0760, 72.8777)
        # We will use simple offsets to simulate donors spread around the area
        mock_donors = [
            ("Rahul Sharma", "O+", "+91 98765 43210", "rahul@email.com", 19.0820, 72.8890, (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'), 1),
            ("Priya Patel", "A-", "+91 98234 56789", "priya@email.com", 19.0650, 72.8550, (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d'), 1),
            ("Amit Verma", "AB+", "+91 98123 45678", "amit@email.com", 19.0980, 72.8640, (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'), 1), # not eligible due to 10 days ago donation
            ("Sneha Reddy", "O-", "+91 99887 76655", "sneha@email.com", 19.0520, 72.8820, (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'), 1),
            ("Vikram Singh", "B+", "+91 97654 32109", "vikram@email.com", 19.0430, 72.8450, None, 1), # never donated before
            ("Ananya Das", "B-", "+91 95432 10987", "ananya@email.com", 19.1120, 72.8980, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'), 1),
            ("Karan Johar", "A+", "+91 91234 56780", "karan@email.com", 19.0200, 72.8300, (datetime.now() - timedelta(days=75)).strftime('%Y-%m-%d'), 1),
            ("Neha Gupta", "O-", "+91 93456 78901", "neha@email.com", 19.1300, 72.8700, None, 0) # Unavailable manually
        ]
        cursor.executemany('''
            INSERT INTO donors (name, blood_group, contact, email, latitude, longitude, last_donation_date, availability)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', mock_donors)
        
    # Seed some dummy requests if empty
    cursor.execute("SELECT COUNT(*) FROM requests")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now().isoformat()
        mock_requests = [
            ("Rajesh Mehta", "City Hospital", "O+", 3, "Critical", 19.0760, 72.8777, "Pending", now_str),
            ("Suman Rao", "Metro Clinic", "B+", 2, "High", 19.0920, 72.8520, "Pending", now_str),
            ("John Doe", "St. Jude Hospital", "AB-", 1, "Medium", 19.0350, 72.8600, "Matched", now_str)
        ]
        cursor.executemany('''
            INSERT INTO requests (patient_name, hospital_name, blood_group, units_needed, urgency, latitude, longitude, status, date_created)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', mock_requests)
        
    conn.commit()
    conn.close()

# Helper function to calculate distance using Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth's radius in kilometers
    try:
        lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 2)
    except Exception:
        return 999.9

# Donors CRUD operations
def get_all_donors():
    conn = get_db_connection()
    donors = conn.execute("SELECT * FROM donors ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(d) for d in donors]

def add_donor(name, blood_group, contact, email, latitude, longitude, last_donation_date=None, availability=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO donors (name, blood_group, contact, email, latitude, longitude, last_donation_date, availability)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, blood_group, contact, email, latitude, longitude, last_donation_date, availability))
    conn.commit()
    donor_id = cursor.lastrowid
    conn.close()
    return donor_id

def update_donor_availability(donor_id, availability):
    conn = get_db_connection()
    conn.execute("UPDATE donors SET availability = ? WHERE id = ?", (availability, donor_id))
    conn.commit()
    conn.close()

def delete_donor(donor_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM donors WHERE id = ?", (donor_id,))
    conn.commit()
    conn.close()

# Requests CRUD operations
def get_all_requests():
    conn = get_db_connection()
    reqs = conn.execute("SELECT * FROM requests ORDER BY date_created DESC").fetchall()
    conn.close()
    return [dict(r) for r in reqs]

def add_request(patient_name, hospital_name, blood_group, units_needed, urgency, latitude, longitude):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO requests (patient_name, hospital_name, blood_group, units_needed, urgency, latitude, longitude, status, date_created)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
    ''', (patient_name, hospital_name, blood_group, units_needed, urgency, latitude, longitude, now_str))
    conn.commit()
    req_id = cursor.lastrowid
    conn.close()
    return req_id

def update_request_status(request_id, status):
    conn = get_db_connection()
    conn.execute("UPDATE requests SET status = ? WHERE id = ?", (status, request_id))
    conn.commit()
    conn.close()

def delete_request(request_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM requests WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()

# Inventory CRUD operations
def get_inventory():
    conn = get_db_connection()
    inv = conn.execute("SELECT * FROM inventory").fetchall()
    conn.close()
    return {row['blood_group']: row['units_available'] for row in inv}

def update_inventory(blood_group, units):
    conn = get_db_connection()
    now_str = datetime.now().isoformat()
    conn.execute('''
        INSERT INTO inventory (blood_group, units_available, last_updated)
        VALUES (?, ?, ?)
        ON CONFLICT(blood_group) DO UPDATE SET units_available = ?, last_updated = ?
    ''', (blood_group, units, now_str, units, now_str))
    conn.commit()
    conn.close()

# Smart donor matching algorithm
def find_matches_for_request(request_id):
    conn = get_db_connection()
    
    # Get request details
    req = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
    if not req:
        conn.close()
        return []
        
    req = dict(req)
    req_bg = req['blood_group']
    req_lat = req['latitude']
    req_lon = req['longitude']
    
    # Allowed blood groups for donor according to compatibility matrix
    compatible_groups = COMPATIBILITY_MATRIX.get(req_bg, [])
    
    # Get all donors that are compatible and active (availability = 1)
    # Filter placeholder syntax for SQL IN clause
    placeholders = ','.join('?' for _ in compatible_groups)
    query = f"SELECT * FROM donors WHERE blood_group IN ({placeholders}) AND availability = 1"
    donors = conn.execute(query, compatible_groups).fetchall()
    
    matched_donors = []
    today = datetime.now().date()
    
    for d in donors:
        d = dict(d)
        
        # Calculate eligibility
        # Rule: A donor is eligible if last_donation_date is NULL or >= 56 days ago
        is_eligible = True
        days_since_donation = 999
        
        if d['last_donation_date']:
            try:
                last_donation = datetime.strptime(d['last_donation_date'], '%Y-%m-%d').date()
                delta = today - last_donation
                days_since_donation = delta.days
                if days_since_donation < 56:
                    is_eligible = False
            except Exception:
                pass
                
        # Calculate distance
        distance = calculate_distance(req_lat, req_lon, d['latitude'], d['longitude'])
        
        # Calculate matching score (higher is better)
        # Criteria: Eligible first, then proximity, then more time since last donation
        score = 0
        if is_eligible:
            score += 100
            # Proximity component: max 50 points, decreasing by 5 points per km
            proximity_score = max(0, 50 - int(distance * 5))
            score += proximity_score
            # Recency component: donors who haven't donated in a while are prioritized
            # (days_since_donation capped at 365 for score calculation)
            recency_score = min(20, days_since_donation // 10)
            score += recency_score
        else:
            # Not eligible right now
            score += max(0, 10 - int(distance * 2))
            
        matched_donors.append({
            'id': d['id'],
            'name': d['name'],
            'blood_group': d['blood_group'],
            'contact': d['contact'],
            'email': d['email'],
            'latitude': d['latitude'],
            'longitude': d['longitude'],
            'distance_km': distance,
            'last_donation_date': d['last_donation_date'],
            'days_since_donation': days_since_donation if days_since_donation != 999 else "None",
            'is_eligible': is_eligible,
            'match_score': round(score, 1)
        })
        
    conn.close()
    
    # Sort matched donors by score descending, then distance ascending
    matched_donors.sort(key=lambda x: (-x['match_score'], x['distance_km']))
    return matched_donors

# Stats calculations for dashboard
def get_dashboard_stats():
    conn = get_db_connection()
    
    total_donors = conn.execute("SELECT COUNT(*) FROM donors").fetchone()[0]
    total_eligible = 0
    today = datetime.now().date()
    
    donors = conn.execute("SELECT last_donation_date, availability FROM donors").fetchall()
    for d in donors:
        if d['availability'] == 1:
            if not d['last_donation_date']:
                total_eligible += 1
            else:
                try:
                    last_donation = datetime.strptime(d['last_donation_date'], '%Y-%m-%d').date()
                    if (today - last_donation).days >= 56:
                        total_eligible += 1
                except Exception:
                    total_eligible += 1
                    
    active_requests = conn.execute("SELECT COUNT(*) FROM requests WHERE status = 'Pending'").fetchone()[0]
    critical_requests = conn.execute("SELECT COUNT(*) FROM requests WHERE status = 'Pending' AND urgency = 'Critical'").fetchone()[0]
    
    # Calculate low stock warnings (if inventory < 5 units)
    inventory = conn.execute("SELECT * FROM inventory").fetchall()
    low_stock_groups = []
    total_stock_units = 0
    for row in inventory:
        total_stock_units += row['units_available']
        if row['units_available'] < 5:
            low_stock_groups.append(row['blood_group'])
            
    conn.close()
    
    return {
        'total_donors': total_donors,
        'eligible_donors': total_eligible,
        'active_requests': active_requests,
        'critical_requests': critical_requests,
        'total_stock_units': total_stock_units,
        'low_stock_groups': low_stock_groups
    }

# Initialize db file on import
if not os.path.exists(DATABASE_PATH):
    init_db()
