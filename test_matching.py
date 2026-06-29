import database
from datetime import datetime

def run_test():
    print("====================================================")
    print("Testing Smart Blood Donation Matching System Engine")
    print("====================================================")
    
    # 1. Initialize Database & Seed
    print("\n[Step 1] Initializing SQLite database...")
    database.init_db()
    print("[SUCCESS] SQLite DB Initialized successfully.")
    
    # 2. Query all donors
    print("\n[Step 2] Querying registered donors...")
    donors = database.get_all_donors()
    print(f"[SUCCESS] Found {len(donors)} seeded donors in registry:")
    for d in donors:
        status = "Available" if d['availability'] == 1 else "Unavailable"
        print(f"   - {d['name']} ({d['blood_group']}) | Last Donated: {d['last_donation_date']} | Status: {status}")
        
    # 3. Log a test blood request
    print("\n[Step 3] Logging a new urgent patient blood request...")
    # Patient requires O+ blood at a hospital in Mumbai (coord: 19.0760, 72.8777)
    req_id = database.add_request(
        patient_name="Test Patient (O+)",
        hospital_name="Apex Care Hospital",
        blood_group="O+",
        units_needed=2,
        urgency="Critical",
        latitude=19.0760,
        longitude=72.8777
    )
    print(f"[SUCCESS] Request logged successfully with ID: {req_id}")
    
    # 4. Run Smart Match compatibility algorithm
    print("\n[Step 4] Running smart matching algorithm...")
    matches = database.find_matches_for_request(req_id)
    print(f"[SUCCESS] Found {len(matches)} potential matching donors (ordered by suitability score):")
    
    for i, m in enumerate(matches, 1):
        eligibility = "ELIGIBLE" if m['is_eligible'] else "RESTING"
        print(f"   {i}. Donor: {m['name']} ({m['blood_group']})")
        print(f"      - Compatibility Score: {m['match_score']}")
        print(f"      - Proximity Distance: {m['distance_km']} km")
        print(f"      - Eligibility: {eligibility} (Days since donation: {m['days_since_donation']})")
        print(f"      - Contact: {m['contact']}")
        
    # 5. Clean up test request
    print("\n[Step 5] Cleaning up test request...")
    database.delete_request(req_id)
    print("[SUCCESS] Cleaned up test request successfully.")
    
    print("\n====================================================")
    print("[SUCCESS] All engine tests completed successfully!")
    print("====================================================")

if __name__ == "__main__":
    run_test()
