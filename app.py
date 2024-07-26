import os
from flask import Flask, request, redirect, url_for, flash, render_template, send_from_directory
from werkzeug.utils import secure_filename
import csv
from datetime import datetime
from collections import defaultdict
from datetime import datetime, timedelta

# Configuration Constants
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), 'processed')
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB
OUTLIER_THRESHOLD = 1000

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_DIR'] = PROCESSED_DIR
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.secret_key = 'super secret key'

# Helper functions
def allowed_file(filename):
    """ Check if file extension is allowed. """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_csv(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return [row for row in reader]
    except UnicodeDecodeError:
        try:
            # Trying with a different encoding
            with open(file_path, 'r', encoding='latin1') as file:
                reader = csv.DictReader(file)
                return [row for row in reader]
        except Exception as e:
            print("Failed to read the file with alternate encoding:", e)
            return None
        
def clean_and_save_data(data):
    """ Clean data by filtering out entries outside of daylight hours and outliers, then save to processed directory based on sorted data and intervals from the first row, including device name. """
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    processed_data = defaultdict(list)
    fieldnames_set = set(['Device'])  # Start with 'Device' field
    unique_dates = set()

    # Convert all rows to dictionary format and parse datetime
    for row in data:
        row['Timestamp'] = datetime.strptime(f"{row['Date']} {row['Time']}", '%Y-%m-%d %H:%M:%S')
    
    # Sort data by timestamp
    data.sort(key=lambda x: x['Timestamp'])

    interval_entries = defaultdict(list)

    # Initialize the first interval reference
    if data:
        interval_reference = data[0]['Timestamp'].replace(minute=(data[0]['Timestamp'].minute // 5) * 5, second=0, microsecond=0)

    for row in data:
        timestamp = row['Timestamp']
        if 6 <= timestamp.hour <= 18:  # Only between 6 AM and 6 PM
            intensity = float(row.get('Value 1', 0))
            if intensity <= OUTLIER_THRESHOLD:  # Check intensity threshold
                # Find the correct half-hour interval for the current timestamp
                while interval_reference + timedelta(minutes=5) <= timestamp:
                    interval_reference += timedelta(minutes=5)
                
                # Store entries by interval
                interval_entries[interval_reference].append(row)
                fieldnames_set.update(row.keys())
                unique_dates.add(timestamp.date())

    # Select the closest entry for each interval
    for interval, entries in interval_entries.items():
        if entries:
            closest_entry = min(entries, key=lambda x: abs((x['Timestamp'] - interval).total_seconds()))
            processed_data[interval.date()].append(closest_entry)

    # Write the processed data to CSV files using the device_name_dd_mm_yyyy format
    for date, rows in processed_data.items():
        for row in rows:
            filename = f"{row['Device']}_{date.strftime('%d-%m-%Y')}.csv"  # Updated to match your required format
            filepath = os.path.join(PROCESSED_DIR, filename)
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = sorted(list(fieldnames_set))
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

    return unique_dates

import os

def delete_data(date, device_name=None):
    processed_files = os.listdir(app.config['PROCESSED_DIR'])
    files_to_delete = []

    if device_name:
        # Delete specific device data for the given date
        filename = f"{device_name}_{date}.csv"
        if filename in processed_files:
            files_to_delete.append(filename)
    else:
        # Delete all device data for the given date
        files_to_delete = [f for f in processed_files if f.endswith(f'{date}.csv')]

    if not files_to_delete:
        return False

    for filename in files_to_delete:
        file_path = os.path.join(app.config['PROCESSED_DIR'], filename)
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {filename}: {str(e)}")
            return False

    return True

from flask import flash

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Retrieve the file from the form data
        file = request.files.get('file')
        # Retrieve the device name from the form data
        device_name = request.form.get('device_name')

        # Check if the file exists and if its extension is allowed
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Ensure the upload directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Save the file to the designated path
            file.save(save_path)
            raw_data = read_csv(save_path)

            # If data is read successfully
            if raw_data:
                # Append the device name to each row of the data
                for row in raw_data:
                    row['Device'] = device_name

            # Clean and save the processed data
            dates = clean_and_save_data(raw_data)

            # Provide feedback to the user based on the process outcome
            if dates:
                flash(f'File processed and saved successfully. Data contains {len(dates)} unique dates from {device_name}.', 'success')
            else:
                flash('No valid data in the file or no daytime data found.', 'error')
            return redirect(url_for('upload_file'))

        # Handle the case where the file is not present or the type is incorrect
        flash('Invalid file part or file type. Only CSV files are allowed.', 'error')
    
    # Render the upload form
    return render_template('index.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route('/visualize')
def visualize_data():
    processed_files = os.listdir(app.config['PROCESSED_DIR'])
    processed_files.sort()
    datasets = defaultdict(lambda: {'data': [], 'labels': []})
    all_labels = set()
    total_watt_hours = defaultdict(float)

    for filename in processed_files:
        device_name = filename.split('_')[0]  # Assume filename format is 'deviceName_date.csv'
        filepath = os.path.join(app.config['PROCESSED_DIR'], filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                prev_timestamp = None
                for row in reader:
                    timestamp = datetime.strptime(f"{row['Date']} {row['Time']}", '%Y-%m-%d %H:%M:%S')
                    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M')
                    all_labels.add(formatted_timestamp)
                    datasets[device_name]['labels'].append(formatted_timestamp)
                    value = float(row['Value 1'])
                    datasets[device_name]['data'].append(value)
                    
                    # Calculate watt-hours
                    if prev_timestamp:
                        time_diff = (timestamp - prev_timestamp).total_seconds() / 3600  # Convert to hours
                        total_watt_hours[device_name] += value * time_diff
                    
                    prev_timestamp = timestamp
        except Exception as e:
            print(f"Failed to read {filename} due to an error: {e}")

    # Sort all labels
    all_labels = sorted(list(all_labels))

    # Normalize data lengths and align with all_labels
    for device_name, device_data in datasets.items():
        aligned_data = [None] * len(all_labels)
        for label, value in zip(device_data['labels'], device_data['data']):
            aligned_data[all_labels.index(label)] = value
        datasets[device_name]['data'] = aligned_data

    # Round total_watt_hours to 2 decimal places
    total_watt_hours = {device: round(wh, 2) for device, wh in total_watt_hours.items()}

    return render_template('visualize.html', datasets=datasets, all_labels=all_labels, total_watt_hours=total_watt_hours)


@app.route('/dates')
def list_dates():
    try:
        files = os.listdir(app.config['PROCESSED_DIR'])
        date_devices = defaultdict(set)
        for file in files:
            if file.endswith('.csv'):
                device_name, date_part = file.split('_')
                date = date_part.split('.')[0]
                date_devices[date].add(device_name)
        
        sorted_dates = sorted(date_devices.keys(), reverse=True)
        return render_template('list_dates.html', date_devices=date_devices, dates=sorted_dates)
    except Exception as e:
        flash(f"Error listing dates: {str(e)}", 'error')
        return redirect(url_for('upload_file'))
    
@app.route('/delete/<date>', methods=['POST'])
def delete_data_route(date):
    device_name = request.form.get('device_name')
    if delete_data(date, device_name):
        if device_name:
            flash(f"Data for device {device_name} on {date} has been deleted.", 'success')
        else:
            flash(f"All data for {date} has been deleted.", 'success')
    else:
        flash("Failed to delete data. Please try again.", 'error')
    return redirect(url_for('list_dates'))
    
from flask import jsonify
@app.route('/visualize/<date>')
def visualize_date(date):
    processed_files = os.listdir(app.config['PROCESSED_DIR'])
    relevant_files = [f for f in processed_files if f.endswith(f'{date}.csv')]
    
    if not relevant_files:
        flash("No data available for this date.", 'error')
        return redirect(url_for('list_dates'))

    datasets = {}
    all_labels = set()
    total_watt_hours = {}
    
    for filename in relevant_files:
        device_name = filename.split('_')[0]
        filepath = os.path.join(app.config['PROCESSED_DIR'], filename)
        try:
            with open(filepath, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                data = []
                labels = []
                total_watts = 0
                prev_timestamp = None
                for row in reader:
                    timestamp = datetime.strptime(f"{row['Date']} {row['Time']}", '%Y-%m-%d %H:%M:%S')
                    formatted_time = timestamp.strftime('%H:%M')
                    labels.append(formatted_time)
                    all_labels.add(formatted_time)
                    value = float(row['Value 1'])
                    data.append(value)
                    
                    # Calculate watt-hours
                    if prev_timestamp:
                        time_diff = (timestamp - prev_timestamp).total_seconds() / 3600  # Convert to hours
                        total_watts += value * time_diff
                    
                    prev_timestamp = timestamp

                datasets[device_name] = {'data': data, 'labels': labels}
                total_watt_hours[device_name] = round(total_watts, 2)
        except Exception as e:
            flash(f"Error reading the file {filename}: {str(e)}", 'error')
            # Initialize with zero if there's an error
            datasets[device_name] = {'data': [], 'labels': []}
            total_watt_hours[device_name] = 0

    if not datasets:
        flash("No valid data found for this date.", 'error')
        return redirect(url_for('list_dates'))

    all_labels = sorted(list(all_labels))

    # Align data with all_labels
    for device_name, device_data in datasets.items():
        aligned_data = [None] * len(all_labels)
        for label, value in zip(device_data['labels'], device_data['data']):
            aligned_data[all_labels.index(label)] = value
        datasets[device_name]['data'] = aligned_data

    return render_template('visualize.html', datasets=datasets, all_labels=all_labels, date=date, total_watt_hours=total_watt_hours)

@app.errorhandler(413)
def error_request_entity_too_large(error):
    return 'File Too Large', 413

if __name__ == '__main__':
    app.run(debug=True)