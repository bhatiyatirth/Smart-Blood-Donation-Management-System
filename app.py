from flask import Flask, jsonify, request, render_template
import database
import os

app = Flask(__name__)

# Initialize DB
database.init_db()

# --- Page Routes ---

@app.route('/')
@app.route('/dashboard')
def dashboard_page():
    return render_template('index.html', active_page='dashboard')

@app.route('/donors')
def donors_page():
    return render_template('donors.html', active_page='donors')

@app.route('/requests')
def requests_page():
    return render_template('requests.html', active_page='requests')

@app.route('/inventory')
def inventory_page():
    return render_template('inventory.html', active_page='inventory')


# --- API Endpoints ---

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = database.get_dashboard_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/donors', methods=['GET', 'POST'])
def handle_donors():
    if request.method == 'GET':
        try:
            donors = database.get_all_donors()
            return jsonify(donors), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    elif request.method == 'POST':
        try:
            data = request.json
            name = data.get('name')
            blood_group = data.get('blood_group')
            contact = data.get('contact')
            email = data.get('email', '')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            last_donation_date = data.get('last_donation_date') or None
            availability = data.get('availability', 1)
            
            if not all([name, blood_group, contact, latitude, longitude]):
                return jsonify({'error': 'Missing required fields (name, blood_group, contact, latitude, longitude)'}), 400
                
            donor_id = database.add_donor(
                name=name,
                blood_group=blood_group,
                contact=contact,
                email=email,
                latitude=latitude,
                longitude=longitude,
                last_donation_date=last_donation_date,
                availability=availability
            )
            return jsonify({'message': 'Donor registered successfully', 'donor_id': donor_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/donors/toggle/<int:donor_id>', methods=['POST'])
def toggle_donor(donor_id):
    try:
        data = request.json
        availability = data.get('availability')
        if availability is None or availability not in [0, 1]:
            return jsonify({'error': 'Invalid availability value'}), 400
            
        database.update_donor_availability(donor_id, availability)
        return jsonify({'message': 'Donor availability updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/donors/<int:donor_id>', methods=['DELETE'])
def remove_donor(donor_id):
    try:
        database.delete_donor(donor_id)
        return jsonify({'message': 'Donor deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/requests', methods=['GET', 'POST'])
def handle_requests():
    if request.method == 'GET':
        try:
            reqs = database.get_all_requests()
            return jsonify(reqs), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    elif request.method == 'POST':
        try:
            data = request.json
            patient_name = data.get('patient_name')
            hospital_name = data.get('hospital_name')
            blood_group = data.get('blood_group')
            units_needed = data.get('units_needed')
            urgency = data.get('urgency')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if not all([patient_name, hospital_name, blood_group, units_needed, urgency, latitude, longitude]):
                return jsonify({'error': 'Missing required fields'}), 400
                
            req_id = database.add_request(
                patient_name=patient_name,
                hospital_name=hospital_name,
                blood_group=blood_group,
                units_needed=int(units_needed),
                urgency=urgency,
                latitude=latitude,
                longitude=longitude
            )
            return jsonify({'message': 'Blood request created successfully', 'request_id': req_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/requests/status/<int:request_id>', methods=['POST'])
def update_request_status(request_id):
    try:
        data = request.json
        status = data.get('status')
        if not status or status not in ['Pending', 'Matched', 'Fulfilled', 'Cancelled']:
            return jsonify({'error': 'Invalid status'}), 400
            
        database.update_request_status(request_id, status)
        return jsonify({'message': 'Request status updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/requests/<int:request_id>', methods=['DELETE'])
def remove_request(request_id):
    try:
        database.delete_request(request_id)
        return jsonify({'message': 'Blood request deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/inventory', methods=['GET', 'POST'])
def handle_inventory():
    if request.method == 'GET':
        try:
            inv = database.get_inventory()
            return jsonify(inv), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    elif request.method == 'POST':
        try:
            data = request.json
            blood_group = data.get('blood_group')
            units = data.get('units')
            
            if not blood_group or units is None:
                return jsonify({'error': 'Missing blood_group or units'}), 400
                
            database.update_inventory(blood_group, int(units))
            return jsonify({'message': 'Inventory updated successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/matches/<int:request_id>', methods=['GET'])
def get_matches(request_id):
    try:
        matches = database.find_matches_for_request(request_id)
        return jsonify(matches), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Start the Flask development server
    app.run(debug=True, host='127.0.0.1', port=5000)
