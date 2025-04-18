import os
import random
from datetime import datetime
from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
from db import db 
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key_here')

# -------------------------------------------
# Registration Route
# -------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname    = request.form['firstname']
        lastname     = request.form['lastname']
        phone_number = request.form['phone_number']
        email        = request.form['email']
        password     = request.form['password']
        address      = request.form['address']
        role         = request.form['role']  # expected: 'patient', 'doctor', or 'caregiver'

        if role == 'doctor':
            # Generate a random 7-digit doctor ID
            doctor_id = str(random.randint(1000000, 9999999))
            if db.register_doctor(doctor_id, firstname, lastname, phone_number, email, password, address):
                return redirect(url_for('login'))
            else:
                flash("Error occurred while registering doctor.", "error")
        elif role == 'patient':
            # Generate a random 10-digit patient ID
            patient_id = str(random.randint(1000000000, 9999999999))
            if db.register_patient(patient_id, firstname, lastname, phone_number, email, password, address):
                return redirect(url_for('login'))
            else:
                flash("Error occurred while registering patient.", "error")
        elif role == 'caregiver':
            # Generate a random 7-digit caregiver ID
            caregiver_id = str(random.randint(1000000, 9999999))
            if db.register_caregiver(caregiver_id, firstname, lastname, phone_number, email, password, address):
                return redirect(url_for('login'))
            else:
                flash("Error occurred while registering caregiver.", "error")
        return redirect(url_for('register'))
    return render_template('register.html')

# -------------------------------------------
# Login Route
# -------------------------------------------
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if db.valid_patient_account(email, password):
        patient_id = db.get_patient_id_by_email(email)
        patient = db.get_patient_data(patient_id)
        return jsonify({
            "patient_id": patient[0],
            "first_name": patient[1],
            "last_name": patient[2]
        }), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role     = request.form['role']
        email    = request.form['email']
        password = request.form['password']

        if role == 'doctor':
            if db.valid_doctor_account(email, password):
                session['role']  = role
                session['email'] = email
                return redirect(url_for('doctor'))
            else:
                flash("Invalid credentials for doctor.", "error")
        elif role == 'patient':
            if db.valid_patient_account(email, password):
                session['role']  = role
                session['email'] = email
                return redirect(url_for('patient'))
            else:
                flash("Invalid credentials for patient.", "error")
        elif role == 'caregiver':
            if db.valid_caregiver_account(email, password):
                session['role']  = role
                session['email'] = email
                return redirect(url_for('caregiver'))
            else:
                flash("Invalid credentials for caregiver.", "error")
    return render_template('login.html')

# -------------------------------------------
# Doctor Dashboard
# -------------------------------------------
@app.route('/doctor', methods=['GET', 'POST'])
def doctor():
    if 'role' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))
    
    email     = session.get('email')
    doctor_id = db.get_doctor_id_by_email(email)
    doctor_data = db.get_doctor_data(doctor_id)
    doctor_data_dict = {
        'id': doctor_data[0],
        'first_name': doctor_data[1],
        'last_name': doctor_data[2],
        'email': doctor_data[3],
        'address': doctor_data[6],
        'phone_number': doctor_data[5],
    }
    
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        if patient_id:
            if 'remove_patient' in request.form:
                if db.remove_doctor_for_patient(doctor_id, patient_id):
                    flash(f"Patient {patient_id} removed successfully.", "success")
                else:
                    flash("Failed to remove patient.", "error")
            else:
                new_patient = db.get_patient_by_id(patient_id)
                if new_patient:
                    if new_patient[7] is None:
                        if db.doctor_add_patient(doctor_id, patient_id):
                            flash(f"Patient {new_patient[1]} {new_patient[2]} added successfully.", "success")
                        else:
                            flash("Error adding patient.", "error")
                    else:
                        flash("This patient is already assigned to a doctor.", "error")
                else:
                    flash("Patient does not exist.", "error")
    
    # Retrieve patients assigned to this doctor
    new_patient = db.get_the_doctor_patients(doctor_id)

    return render_template('doctor.html',
                           doctor_data_dict=doctor_data_dict,
                           new_patient=new_patient)

@app.route('/patient_health_data/<patient_id>')
def patient_health_data(patient_id):
    patient = db.get_patient_data(patient_id)
    if not patient:
        flash("Patient not found.", "error")
        return redirect(url_for('doctor'))

    db.raw_query("SELECT device_id FROM icare.patient_device WHERE patient_id = %s;", (patient_id,))
    result = db.fetch_one()
    device_id = result[0] if result else "Not Assigned"

    device = None
    if device_id != "Not Assigned":
        db.raw_query("SELECT * FROM icare.devices WHERE device_id = %s;", (device_id,))
        device = db.fetch_one()

    context = {
        'patient': {
            'id': patient[0],
            'first_name': patient[1],
            'last_name': patient[2],
            'email': patient[3],
            'phone_number': patient[5],
            'address': patient[6]
        },
        'device': {
            'id': device[0] if device else device_id,
            'battery': device[1] if device else "N/A"
        }
    }
    return render_template("patient_healthData.html", **context)

# -------------------------------------------
# Create Caregiver Task (JSON POST)
# -------------------------------------------
@app.route('/create_caregiver_task', methods=['POST'])
def create_caregiver_task():
    data = request.get_json()
    task_description = data.get('description')
    schedule_date    = data.get('schedule_date')
    caregiver_id     = data.get('caregiverId')
    patient_id       = data.get('patientId')
    doctor_id        = data.get('doctorId')
    try:
        scheduled_date = datetime.fromisoformat(schedule_date)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format'}), 400

    if db.add_caregiver_task(task_description, scheduled_date, doctor_id, caregiver_id, patient_id):
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to create caregiver task'}), 400

# -------------------------------------------
# Create Patient Task (JSON POST)
# -------------------------------------------
@app.route('/create_patient_task', methods=['POST'])
def create_patient_task():
    data = request.get_json()
    task_description = data.get('description')
    schedule_date    = data.get('schedule_date')
    patient_id       = data.get('patientId')
    doctor_id        = data.get('doctorId')
    try:
        scheduled_date = datetime.fromisoformat(schedule_date)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format'}), 400

    if db.add_patient_task(task_description, scheduled_date, doctor_id, patient_id):
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to create patient task'}), 400

# -------------------------------------------
# Get Caregiver Tasks Endpoint
# -------------------------------------------
@app.route('/get_caregiver_tasks/<caregiver_id>/<patient_id>', methods=['GET'])
def get_caregiver_tasks(caregiver_id, patient_id):
    try:
        caregiver_tasks = db.get_caregiver_tasks(caregiver_id, patient_id)
        return jsonify({'caregiver_tasks': caregiver_tasks})
    except Exception as e:
        return jsonify({'caregiver_tasks': []}), 500

# -------------------------------------------
# Get Patient Tasks Endpoint
# -------------------------------------------
@app.route('/get_patient_tasks/<patient_id>', methods=['GET'])
def get_patient_tasks(patient_id):
    try:
        tasks = db.get_patient_tasks(patient_id)
        return jsonify({'tasks': tasks})
    except Exception as e:
        return jsonify({'tasks': []}), 500

# -------------------------------------------
# Patient Dashboard
# -------------------------------------------
@app.route('/patient', methods=['GET', 'POST'])
def patient():
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))
    
    email      = session.get('email')
    patient_id = db.get_patient_id_by_email(email)
    patient_data = db.get_patient_data(patient_id)
    caregiver_id = patient_data[8]  # Assuming caregiver_id is stored here
    patient_data_dict = {
        'id': patient_data[0],
        'first_name': patient_data[1],
        'last_name': patient_data[2],
        'email': patient_data[3],
        'address': patient_data[6],
        'phone_number': patient_data[5]
    }
    
    # Retrieve patient tasks
    patient_tasks = []
    tasks_data = db.get_patient_tasks_info(patient_id)
    if tasks_data:
        for data_task in tasks_data:
            patient_tasks.append({
                'patient_task_id': data_task[0],
                'task_description': data_task[1],
                'scheduled_date': data_task[2],
                'status': data_task[3],
                'doctor_id': data_task[4]
            })
    
    # Retrieve caregiver tasks
    caregiver_tasks = []
    caregiver_tasks_data = db.get_caregiver_tasks_info(caregiver_id, patient_id)
    if caregiver_tasks_data:
        for ct in caregiver_tasks_data:
            caregiver_tasks.append({
                'caregiver_task_id': ct[0],
                'task_description': ct[1],
                'scheduled_date': ct[2],
                'status': ct[3],
                'doctor_id': ct[4],
                'caregiver_id': ct[5],
                'patient_id': ct[6]
            })
    
    return render_template('patient.html', 
                           patient_data_dict=patient_data_dict, 
                           patient_tasks=patient_tasks, 
                           caregiver_tasks=caregiver_tasks)

# -------------------------------------------
# Caregiver Dashboard
# -------------------------------------------
@app.route('/caregiver', methods=['GET', 'POST'])
def caregiver():
    if 'role' not in session or session['role'] != 'caregiver':
        return redirect(url_for('login'))
    
    email = session.get('email')
    caregiver_id = db.get_caregiver_id_by_email(email)
    caregiver_data = db.get_caregiver_data(caregiver_id)
    caregiver_data_dict = {
        'caregiver_id': caregiver_data[0],
        'first_name': caregiver_data[1],
        'last_name': caregiver_data[2],
        'email': caregiver_data[3],
        'address': caregiver_data[6],
        'phone_number': caregiver_data[5]
    }
    
    if request.method == 'POST':
        task_id = request.form.get('task_id')
        if task_id:
            if db.update_caregiver_task_status(int(task_id), "Completed"):
                flash("Task marked as completed!", "success")
            else:
                flash("Failed to update task.", "error")
        return redirect(url_for('caregiver'))
    
    caregiver_tasks = []
    caregiver_tasks_data = db.get_a_caregiver_all_tasks_info(caregiver_id)
    if caregiver_tasks_data:
        for ct in caregiver_tasks_data:
            caregiver_tasks.append({
                'caregiver_task_id': ct[0],
                'task_description': ct[1],
                'scheduled_date': ct[2],
                'status': ct[3],
                'doctor_id': ct[4],
                'patient_id': ct[6]
            })
    
    return render_template('caregiver.html', caregiver_data_dict=caregiver_data_dict, caregiver_tasks=caregiver_tasks)

# -------------------------------------------
# Sensor Data Endpoints (for ESP32)
# -------------------------------------------
@app.route('/data/<patient_id>', methods=['GET'])
def get_patient_data(patient_id):
    try:
        print(f"Getting data for patient: {patient_id}")

        # 1. Get device ID
        db.raw_query("SELECT device_id FROM icare.patient_device WHERE patient_id = %s;", (patient_id,))
        result = db.fetch_one()
        print("Device fetch result:", result)

        if not result:
            return jsonify({"status": "error", "message": "No device assigned"}), 404

        device_id = result[0]
        print("Resolved device_id:", device_id)

        # 2. Step Count
        try:
            today_steps = db.get_today_step_count(patient_id)
            print("Today's steps:", today_steps)

            db.raw_query("""
                SELECT date
                FROM icare.step_counting
                WHERE patient_id = %s
                ORDER BY time_seconds DESC
                LIMIT 1;
            """, (patient_id,))
            step_date_result = db.fetch_one()
            step_date_str = step_date_result[0].strftime('%Y-%m-%d') if step_date_result else None
            print("Step count date:", step_date_str)
        except Exception as e:
            db.connection.rollback()
            print("Step count error:", e)
            today_steps = 0

        # 3. Latest vitals
        try:
            db.raw_query("""
                SELECT heart_rate, spo2, temperature
                FROM icare.sensor_data
                WHERE device_id = %s
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (device_id,))
            row = db.fetch_one()
            print("Vitals row:", row)
        except Exception as e:
            db.connection.rollback()
            row = None
            print("Vitals error:", e)

        # 4. Waveform
        try:
            db.raw_query("""
                SELECT waveform_values, peaks
                FROM icare.sensor_waveform
                WHERE device_id = %s
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (device_id,))
            waveform_row = db.fetch_one()
            print("Waveform row:", waveform_row)
            waveform = waveform_row[0] if waveform_row else []
            peaks = waveform_row[1] if waveform_row and waveform_row[1] else []
        except Exception as e:
            db.connection.rollback()
            print("Waveform error:", e)
            waveform = []
            peaks = []

        # 5. Fall detection
        # 1. Fetch latest sensor row
        db.raw_query("""
            SELECT heart_rate, spo2, temperature, fall_detected
            FROM icare.sensor_data
            WHERE device_id = %s
            ORDER BY timestamp DESC
            LIMIT 1;
        """, (device_id,))
        row = db.fetch_one()

        fall_status = row[3] if row else False

        # 2. If fall_status is True, get location
        latitude = None
        longitude = None
        if fall_status:
            db.raw_query("""
                SELECT latitude, longitude
                FROM icare.fall_detection
                WHERE device_id = %s
                ORDER BY time_of_fall DESC
                LIMIT 1;
            """, (device_id,))
            fall_info = db.fetch_one()
            if fall_info:
                latitude = fall_info[0]
                longitude = fall_info[1]

        # Final response
        if row:
            response = {
                "bpm": row[0],
                "spo2": row[1],
                "temperature": row[2],
                "stepCount": today_steps,
                "waveform": waveform,
                "peaks": peaks,
                "fall": fall_status,
                "latitude": latitude,
                "longitude": longitude,
                "stepDate": step_date_str 
            }
            print("Final JSON response:", response)
            return jsonify(response)
        else:
            return jsonify({"status": "error", "message": "No sensor data found"}), 404

    except Exception as e:
        db.connection.rollback()
        print("TOTAL FAILURE:", e)
        return jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"}), 500
    if 'role' not in session or session['role'] != 'patient':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    email = session['email']
    patient_id = db.get_patient_id_by_email(email)

    if not patient_id:
        return jsonify({"status": "error", "message": "Patient not found"}), 404

    # Get the device_id assigned to this patient
    db.raw_query("""
        SELECT device_id FROM icare.patient_device WHERE patient_id = %s;
    """, (patient_id,))
    result = db.fetch_one()

    if not result:
        return jsonify({"status": "error", "message": "No device assigned"}), 404

    device_id = result[0]

    db.raw_query("""
        SELECT heart_rate, spo2, temperature, step_count
        FROM icare.sensor_data
        WHERE device_id = %s
        ORDER BY timestamp DESC
        LIMIT 1;
    """, (device_id,))
    row = db.fetch_one()

    if row:
        data = {
            "bpm": row[0],
            "spo2": row[1],
            "temperature": row[2],
            "stepCount": row[3],
            "waveform": row[4], # Make sure this returns JSON list
            "fall": False  # update this!!!
        }
        return jsonify(data)
    else:
        return jsonify({"status": "error", "message": "No sensor data found"}), 404

@app.route('/postdata', methods=['POST'])
def postdata():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON payload received"}), 400
    try:
        client_id     = data.get("client_id")
        hr            = data.get("hr")
        spo2          = data.get("spo2")
        temperature   = data.get("temperature")
        step_count    = data.get("stepCount")  # cumulative from device
        fall_detected = data.get("fall", False)
        waveform      = data.get("waveform")
        peaks         = data.get("peaks", [])

        now = int(datetime.now().timestamp())

        # Store basic sensor data
        db.raw_query("""
            INSERT INTO icare.sensor_data (device_id, heart_rate, spo2, temperature, step_count, fall_detected)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (client_id, hr, spo2, temperature, step_count, fall_detected))

        # Store waveform
        if waveform and isinstance(waveform, list):
            db.insert_sensor_waveform(client_id, waveform, peaks)

        # Handle step count delta insert
        if step_count is not None:
            # Get patient_id for this device
            db.raw_query("SELECT patient_id FROM icare.patient_device WHERE device_id = %s;", (client_id,))
            result = db.fetch_one()
            patient_id = result[0] if result else None

            if patient_id:
                # Get last known cumulative step_count from sensor_data
                db.raw_query("""
                    SELECT step_count
                    FROM icare.sensor_data
                    WHERE device_id = %s AND step_count IS NOT NULL
                    ORDER BY timestamp DESC
                    OFFSET 1 LIMIT 1;  -- get the second-last to compare previous
                """, (client_id,))
                last_row = db.fetch_one()
                last_count = last_row[0] if last_row else 0

                step_diff = step_count - last_count

                # Handle reset or weird jump
                if step_diff < 0:
                    print(f"[RESET DETECTED] Device likely rebooted. step_count={step_count}, last={last_count}")
                    step_diff = 0

                # Only insert reasonable diffs (e.g., avoid double-counting after reboot)
                if 0 < step_diff <= 200:  # tweak this limit if needed
                    print(f"[STEP INSERT] Added {step_diff} steps.")
                    db.raw_query("""
                        INSERT INTO icare.step_counting (device_id, patient_id, date, time_seconds, step_count, acceleration_mag)
                        VALUES (%s, %s, CURRENT_DATE, %s, %s, %s);
                    """, (client_id, patient_id, now, step_diff, 0.0))
                else:
                    print(f"[SKIPPED] Unreasonable step diff: {step_diff} (step_count={step_count}, last={last_count})")
        
        db.commit()
        return jsonify({"status": "success"}), 200

    except Exception as e:
        db.connection.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/historical_data/<patient_id>/<metric>', methods=['GET'])
def get_historical_data(patient_id, metric):
    # Map metric to DB column
    column_map = {
        'bpm': 'heart_rate',
        'spo2': 'spo2',
        'temperature': 'temperature',
        'stepCount': 'step_count',
        'fall': 'fall_detected'
    }

    if metric not in column_map:
        return jsonify({"status": "error", "message": "Invalid metric"}), 400

    db.raw_query("""
        SELECT timestamp, {} FROM icare.sensor_data
        WHERE device_id = (
            SELECT device_id FROM icare.patient_device WHERE patient_id = %s
        )
        ORDER BY timestamp DESC
        LIMIT 50
    """.format(column_map[metric]), (patient_id,))

    rows = db.fetch_all()
    if rows:
        labels = [r[0].strftime('%Y-%m-%d %H:%M') for r in rows]
        values = [r[1] for r in rows]
        return jsonify({'labels': labels[::-1], 'values': values[::-1]})
    else:
        return jsonify({'labels': [], 'values': []})

@app.route('/fall', methods=['POST'])
def receive_fall():
    data = request.json
    print("Fall alert received:", data)

    device_id = data.get('client_id')
    latitude = data.get('lat')
    longitude = data.get('lon')
    timestamp = data.get('time') or int(datetime.now().timestamp())

    # Validate required fields
    if not device_id:
        return jsonify({"status": "error", "message": "Missing 'client_id' in request"}), 400
    if latitude is None or longitude is None:
        return jsonify({"status": "error", "message": "Missing coordinates (lat/lon) in request"}), 400

    try:
        db.raw_query("""
            INSERT INTO icare.fall_detection (device_id, fall_detected, time_of_fall, latitude, longitude)
            VALUES (%s, TRUE, %s, %s, %s)
        """, (device_id, timestamp, latitude, longitude))
        db.commit()

        return jsonify(status="recorded"), 200
    except Exception as e:
        try:
            db.rollback()
        except Exception as rollback_err:
            print("Rollback failed:", rollback_err)
        print(f"Error inserting fall: {e}")
        return jsonify(status="error", message=str(e)), 500

@app.route('/steps/<device_id>', methods=['GET'])
def get_steps_for_device(device_id):
    db.raw_query("SELECT patient_id FROM icare.patient_device WHERE device_id = %s", (device_id,))
    result = db.fetch_one()
    if result:
        patient_id = result[0]
        steps_today = db.get_today_step_count(patient_id)
        return jsonify({"stepCount": steps_today})
    else:
        return jsonify({"error": "Device not assigned to any patient"}), 404

@app.route("/patient_healthData.html")
def patient_data():
    return render_template("patient_healthData.html")

# -------------------------------------------
# Home / Index Route
# -------------------------------------------
@app.route('/')
@app.route('/index')
def dashboard():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)