import os
from flask import current_app
from deepface import DeepFace
import pandas as pd
from app.models.student import Student

class FaceRecognitionService:
    """Service to handle true AI face recognition using DeepFace."""

    @staticmethod
    def process_classroom_image(image_path):
        """
        Detect and recognize multiple faces in the classroom image by comparing
        them against the students' uploaded profile photos.
        
        Args:
            image_path (str): The absolute path to the uploaded classroom image file.
            
        Returns:
            list: A list of recognized Student objects.
            int: Total number of faces detected in the image.
        """
        # The database path is where all the student profile photos are saved
        db_path = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads/students')
        
        # If there are no photos in the directory, we can't recognize anyone
        if not os.path.exists(db_path) or len([f for f in os.listdir(db_path) if os.path.isfile(os.path.join(db_path, f))]) == 0:
            return [], 0

        try:
            # DeepFace.find searches for all faces in image_path against the db_path
            # It returns a list of pandas DataFrames (one DataFrame per detected face in the classroom image)
            # enforce_detection=False prevents it from throwing an error if NO faces are found at all
            results = DeepFace.find(img_path=image_path, db_path=db_path, enforce_detection=False, silent=True)
        except Exception as e:
            print(f"DeepFace Error: {e}")
            return [], 0

        recognized_students = []
        face_count = len(results)

        for df in results:
            if not df.empty:
                # Get the absolute path of the best match from the 'identity' column
                match_path = df.iloc[0]['identity']
                # Extract just the filename (e.g., 'scan_123.jpg')
                matched_filename = os.path.basename(match_path)

                # Find the student in the database who has this profile photo
                student = Student.query.filter_by(photo_path=matched_filename, is_active=True).first()
                
                if student and student not in recognized_students:
                    recognized_students.append(student)

        return recognized_students, face_count
