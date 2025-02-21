import sqlite3
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)

DATABASE = 'devices.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create the devices table if it doesn't exist.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_number TEXT UNIQUE,
            service_tag TEXT,
            status TEXT DEFAULT 'In Office',
            student_assigned TEXT,
            last_update TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database on startup.
init_db()

@app.route('/')
def index():
    search_query = request.args.get('q', '').strip()
    conn = get_db_connection()
    if search_query:
        search_like = f"%{search_query}%"
        devices = conn.execute(
            "SELECT * FROM devices WHERE inventory_number LIKE ? OR service_tag LIKE ? OR student_assigned LIKE ?",
            (search_like, search_like, search_like)
        ).fetchall()
    else:
        devices = conn.execute('SELECT * FROM devices').fetchall()
    conn.close()
    return render_template('index.html', devices=devices, search_query=search_query)

@app.route('/register_device', methods=['POST'])
def register_device():
    barcode = request.form.get('barcode', '').strip()
    # Expected barcode format: "INV ****** SERV *******"
    pattern = r'^INV\s+([A-Za-z0-9]{6})\s+SERV\s+([A-Za-z0-9]{7})$'
    match = re.match(pattern, barcode)
    if match:
        inventory_number = match.group(1)
        service_tag = match.group(2)
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO devices (inventory_number, service_tag, last_update) VALUES (?, ?, ?)',
                (inventory_number, service_tag, None)
            )
            conn.commit()
            flash('Device registered successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Device with this inventory number already exists.', 'error')
        conn.close()
    else:
        flash('Invalid barcode format for device.', 'error')
    return redirect(url_for('index'))

@app.route('/process_lending', methods=['POST'])
def process_lending():
    device_barcode = request.form.get('device_barcode', '').strip()
    student_barcode = request.form.get('student_barcode', '').strip()
    pattern = r'^INV\s+([A-Za-z0-9]{6})\s+SERV\s+([A-Za-z0-9]{7})$'
    match = re.match(pattern, device_barcode)
    if not match:
        flash('Invalid device barcode format.', 'error')
        return redirect(url_for('index'))
    inventory_number = match.group(1)
    conn = get_db_connection()
    device = conn.execute(
        'SELECT * FROM devices WHERE inventory_number = ?',
        (inventory_number,)
    ).fetchone()
    if not device:
        flash('Device not found in inventory.', 'error')
        conn.close()
        return redirect(url_for('index'))
    
    if device['status'] == 'In Office':
        if not re.match(r'^\d{8}$', student_barcode):
            flash('Invalid student barcode format. It should be 8 digits.', 'error')
            conn.close()
            return redirect(url_for('index'))
        # Prevent a student from having more than one device on loan.
        existing = conn.execute(
            'SELECT * FROM devices WHERE student_assigned = ? AND status = ?',
            (student_barcode, 'On loan')
        ).fetchone()
        if existing:
            flash('This student already has a device on loan.', 'error')
            conn.close()
            return redirect(url_for('index'))
        conn.execute(
            'UPDATE devices SET status = ?, student_assigned = ?, last_update = ? WHERE id = ?',
            ('On loan', student_barcode, datetime.now(), device['id'])
        )
        conn.commit()
        flash('Device loaned to student {}.'.format(student_barcode), 'success')
    elif device['status'] == 'On loan':
        conn.execute(
            'UPDATE devices SET status = ?, student_assigned = NULL, last_update = ? WHERE id = ?',
            ('In Office', None, device['id'])
        )
        conn.commit()
        flash('Device returned and now in office.', 'success')
    else:
        flash('Unknown device status.', 'error')
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:device_id>', methods=['GET', 'POST'])
def edit_device(device_id):
    conn = get_db_connection()
    device = conn.execute('SELECT * FROM devices WHERE id = ?', (device_id,)).fetchone()
    if device is None:
        flash('Device not found.', 'error')
        conn.close()
        return redirect(url_for('index'))
    if request.method == 'POST':
        inventory_number = request.form.get('inventory_number').strip()
        service_tag = request.form.get('service_tag').strip()
        status = request.form.get('status').strip()
        student_assigned = request.form.get('student_assigned').strip()
        if student_assigned == '':
            student_assigned = None
        last_update = datetime.now() if status == 'On loan' else None
        try:
            conn.execute('''
                UPDATE devices
                SET inventory_number = ?,
                    service_tag = ?,
                    status = ?,
                    student_assigned = ?,
                    last_update = ?
                WHERE id = ?
            ''', (inventory_number, service_tag, status, student_assigned, last_update, device_id))
            conn.commit()
            flash('Device updated successfully.', 'success')
        except sqlite3.IntegrityError:
            flash('Inventory number already exists.', 'error')
        conn.close()
        return redirect(url_for('index'))
    conn.close()
    return render_template('edit.html', device=device)

@app.route('/delete/<int:device_id>', methods=['GET'])
def delete_device(device_id):
    conn = get_db_connection()
    device = conn.execute('SELECT * FROM devices WHERE id = ?', (device_id,)).fetchone()
    if device is None:
        flash('Device not found.', 'error')
        conn.close()
        return redirect(url_for('index'))
    conn.execute('DELETE FROM devices WHERE id = ?', (device_id,))
    conn.commit()
    conn.close()
    flash('Device deleted successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/delete_bulk', methods=['POST'])
def delete_bulk():
    selected = request.form.getlist('selected_devices')
    if not selected:
        flash('No devices selected for deletion.', 'error')
        return redirect(url_for('index'))
    conn = get_db_connection()
    for device_id in selected:
        conn.execute('DELETE FROM devices WHERE id = ?', (device_id,))
    conn.commit()
    conn.close()
    flash(f'{len(selected)} devices deleted successfully.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

