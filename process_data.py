import csv
import os
from typing import List, Dict, Tuple
from datetime import datetime, time, timedelta
from collections import defaultdict

PROCESSED_DIR = 'processed'
OUTLIER_THRESHOLD = 1000

def read_csv(file_path: str) -> List[Dict]:
    """
    Read data from a CSV file and return it as a list of dictionaries.
    """
    data = []
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return data

    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

def clean_data(data: List[Dict]) -> List[Dict]:
    """
    Clean the data by combining date and time into a timestamp and removing nighttime readings (considered as noise).
    Assumes the data has 'Date' and 'Time' fields and combines them into a 'timestamp'.
    """
    cleaned_data = []
    for row in data:
        date_time_str = f"{row['Date']} {row['Time']}"
        timestamp = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
        if time(6, 0) <= timestamp.time() <= time(18, 0):  # Daytime: 6 AM to 6 PM
            row['timestamp'] = timestamp
            cleaned_data.append(row)
    return cleaned_data

def analyze_data(data: List[Dict]) -> Dict:
    """
    Perform detailed analysis on the cleaned solar panel data.
    Assumes data has a 'Value 1' field for solar intensity.
    """
    if not data:
        return {"error": "No data to analyze"}

    intensities = [float(row['Value 1']) for row in data if 'Value 1' in row]
    valid_intensities = [i for i in intensities if i <= OUTLIER_THRESHOLD]
    
    return {
        "total_readings": len(data),
        "average_solar_intensity": sum(valid_intensities) / len(valid_intensities) if valid_intensities else 0,
        "max_solar_intensity": max(valid_intensities) if valid_intensities else 0,
        "min_solar_intensity": min(valid_intensities) if valid_intensities else 0,
        "daytime_readings": len(data),
        "outliers": len(intensities) - len(valid_intensities)
    }

def prepare_chart_data(data: List[Dict]) -> Tuple[List[str], List[float], List[Dict]]:
    """
    Prepare data for the Chart.js implementation, including handling of outliers.
    Samples data every 10 minutes.
    Returns a tuple of labels (timestamps), solar intensity values, and outliers.
    """
    sampled_data = defaultdict(list)
    for row in data:
        timestamp = row['timestamp']
        rounded_timestamp = timestamp.replace(minute=timestamp.minute // 10 * 10, second=0, microsecond=0)
        sampled_data[rounded_timestamp].append(float(row['Value 1']))

    labels = []
    values = []
    outliers = []

    for timestamp, intensities in sorted(sampled_data.items()):
        avg_intensity = sum(intensities) / len(intensities)
        label = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        labels.append(label)
        
        if avg_intensity > OUTLIER_THRESHOLD:
            outliers.append({'x': label, 'y': avg_intensity})
            values.append(OUTLIER_THRESHOLD)  # Cap at OUTLIER_THRESHOLD for main dataset
        else:
            values.append(avg_intensity)

    return labels, values, outliers

def save_processed_data(data: List[Dict]):
    """
    Save processed data into daily CSV files in the processed directory.
    """
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    daily_data = defaultdict(list)
    for row in data:
        date = row['timestamp'].date()
        daily_data[date].append(row)

    for date, rows in daily_data.items():
        filename = f"{date.strftime('%d_%m_%Y')}.csv"
        filepath = os.path.join(PROCESSED_DIR, filename)
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = rows[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

def main():
    data_file = 'data/sample-data.csv'
    raw_data = read_csv(data_file)
    
    if raw_data:
        cleaned_data = clean_data(raw_data)
        save_processed_data(cleaned_data)
        analysis_result = analyze_data(cleaned_data)
        print("Analysis Results:")
        for key, value in analysis_result.items():
            print(f"{key}: {value}")
        print(f"Removed nighttime readings: {len(raw_data) - len(cleaned_data)}")
        
        # Prepare chart data
        labels, values, outliers = prepare_chart_data(cleaned_data)
        print(f"Prepared {len(labels)} data points for the chart")
        print(f"Identified {len(outliers)} outliers")
        
        # Here you would typically pass labels, values, and outliers to your template rendering function
        # For example:
        # render_template('acknowledgement.html', labels=labels, values=values, outliers=outliers)
    else:
        print("No data to analyze. Please ensure the CSV file is present and contains valid data.")

if __name__ == "__main__":
    main()
