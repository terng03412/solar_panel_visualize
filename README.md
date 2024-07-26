# Solar Panel Data Analysis System

## Overview

This application facilitates the uploading, processing, and visualization of solar panel data collected from various devices. It provides insights into the optimal placement and performance of solar panels based on solar intensity measurements.

## Features

- **Data Upload**: Allows users to upload CSV files containing solar panel data.
- **Data Processing**: Cleans and filters the data to exclude nighttime readings and outliers. Processes data to fit into specified intervals.
- **Data Visualization**: Offers detailed charts displaying solar intensity over time and calculates total energy generation in watt-hours.
- **Date Management**: Allows users to view data by date and delete data entries as needed.

## Technology Stack

- **Flask**: A micro web framework for Python.
- **Chart.js**: Used for rendering interactive charts.
- **HTML/CSS**: For the front-end interface.
- **JavaScript**: Enhances the front-end interactivity, particularly in handling file uploads and visualizations.

## Project Structure
/your-project-directory
|-- app.py # Main Flask application file with routes
|-- process_data.py # Module for processing uploaded CSV data
|-- templates/ # Folder containing HTML templates
|-- index.html # Home page and upload form
|-- list_dates.html # Page for displaying available data dates
|-- visualize.html # Visualization page
|-- static/ # Contains CSS and potentially JavaScript files


## Setup and Installation

1. **Clone the repository**
   ```bash
   git clone https://your-repository-url.git
   cd your-project-directory

2. **Set up a virtual environment (optional but recommended)**
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

3. **Install the dependencies**
pip install -r requirements.txt

4. **Run the application**
python app.py

5. **Access the application**
Open your browser and go to http://127.0.0.1:5000.

##  Usage

Uploading Data: Navigate to the home page, input the device name, and upload a CSV file.
Viewing Data: Click on 'View All Data' to see the visualizations or 'View by Date' to select specific dates for detailed data inspection.

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your updates.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.

### Notes

- You might need to create a `requirements.txt` file listing all necessary Python packages (e.g., Flask, numpy).
- Ensure you update the repository URL and any specific commands based on your actual project setup.

This README provides a general template. You can customize it further based on your project's specifics and requirements.
