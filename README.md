# AI Classroom Intelligence System

An intelligent, Flask-based web application that uses Artificial Intelligence, Computer Vision, and Analytics to monitor classroom activities, track attendance, and generate actionable insights in real time.

## Features

*   **Modern Dashboard:** Premium SaaS-style dashboard with glassmorphism design, dark/light mode toggle, and responsive layout.
*   **Real-time AI Detection:** Integrates with YOLOv8 (or runs in simulation mode) to count students and monitor classroom occupancy.
*   **Attendance Analytics:** Tracks daily, weekly, monthly, and semester attendance rates.
*   **Smart AI Insights:** Automatically generates natural language insights and recommendations based on attendance trends and classroom utilization.
*   **Student Risk Detection:** Identifies at-risk students based on attendance thresholds and consecutive absences.
*   **Predictive Analytics:** Uses machine learning (Linear Regression) to forecast future attendance trends.
*   **Comprehensive Reporting:** Export attendance data to PDF, Excel, or CSV formats.
*   **Role-Based Access Control:** Secure authentication system for Admins, Teachers, and Students.

## Prerequisites

*   Python 3.8+
*   Virtual Environment (recommended)

## Installation & Setup

1.  **Clone the repository and navigate to the project directory:**

    ```bash
    cd "AI CLASSROOM INTELLEGENCE SYSTEM"
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Seed the Database:**

    Run the seeder script to create the SQLite database, populate it with 50 sample students, 30 days of attendance history, and default user accounts.

    ```bash
    python seed_data.py
    ```

5.  **Run the Application:**

    ```bash
    python app.py
    ```

6.  **Access the Dashboard:**

    Open your web browser and navigate to `http://localhost:5000`.

    *   **Username:** `admin`
    *   **Password:** `admin123`

## Configuration

The application uses a `.env` file and `config.py` for configuration.

*   `USE_SIMULATION`: Set to `True` (default) to run the app using generated mock data for camera detection. Set to `False` to use a real webcam and YOLOv8 model.
*   To use the real YOLO model, ensure you have the `ultralytics` package installed and place the `yolov8n.pt` model file in the `ai_models/` directory.

## Project Structure

*   `app/`: Main application package (Models, Routes, Services, Templates, Static).
*   `instance/`: Contains the SQLite database file (`classroom.db`).
*   `data/reports/`: Directory where generated PDF/Excel reports are saved.
*   `seed_data.py`: Script to populate the database.
*   `app.py`: Application entry point.

## Student Detection / Head Count

### Most suitable:

YOLOv8
YOLOv11 (newer versions if available in your environment)

### Purpose:

* Count students
* Detect occupied seats
* Classroom occupancy analysis
* Real-time camera monitoring

## Face Recognition Attendance

### Models:

* FaceNet
* DeepFace
* Dlib Face Recognition

### Purpose:

* Identify individual students
* Mark attendance automatically

## Attendance Prediction

### Machine Learning Models:

* Random Forest
* XGBoost

### Input:

* Historical attendance
* Day of week
* Semester
* Subject

## Student Risk Detection

### Models:

* Random Forest
* XGBoost
*   Logistic Regression

### Purpose:

* Detect students likely to fall below attendance requirements.     

## Classroom Engagement Analysis (Advanced)

### Models:

* MediaPipe
* OpenPose

### Purpose:

* Estimate attention
* Detect raised hands
* Analyze movement patterns