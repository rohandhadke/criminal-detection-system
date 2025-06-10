from datetime import datetime
import cv2
import pickle
import os
import time
import pymongo
from pymongo import MongoClient

# Initialize MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['criminal_detection_system']

def recognize_face_from_webcam(timeout=10):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    model_path = os.path.join(os.path.dirname(__file__), "criminal_trained_model.yml")
    recognizer.read(model_path)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    labels_path = os.path.join(base_dir, 'trainer', 'labels.pickle')

    if not os.path.exists(labels_path):
        print(f"[ERROR] File not found: {labels_path}")
        return "FileNotFound"

    with open(labels_path, "rb") as f:
        labels = pickle.load(f)
        labels = {v: k for k, v in labels.items()}

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cam = cv2.VideoCapture(0)

    detected_criminal = None
    start_time = time.time()

    while True:
        ret, frame = cam.read()
        if not ret:
            print("[ERROR] Failed to grab frame")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            roi = gray[y:y+h, x:x+w]
            id_, conf = recognizer.predict(roi)

            if conf < 60:  # Confidence threshold
                name = labels[id_]
                print(f"[MATCH] Face matched with: {name} (Confidence: {conf:.2f})")
                detected_criminal = name
                
                # Save the detected criminal's image
                detected_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'detected_criminals')
                os.makedirs(detected_dir, exist_ok=True)
                
                # Get the next number for the filename
                existing_files = [f for f in os.listdir(detected_dir) if f.startswith('detected_') and f.endswith('.jpg')]
                if existing_files:
                    numbers = [int(f.split('_')[1].split('.')[0]) for f in existing_files]
                    next_num = max(numbers) + 1
                else:
                    next_num = 1
                
                # Create new filename with the next number
                filename = f"detected_{next_num}.jpg"
                filepath = os.path.join('static', 'detected_criminals', filename).replace('\\', '/')
                
                # Save the frame with the detected face
                cv2.imwrite(os.path.join(detected_dir, filename), frame)
                print(f"[INFO] Saved detected criminal image to: {filepath}")
                
                print("filepath from face_matcher.py", filepath)
                print("filename from face_matcher.py", filename)
                
                cam.release()
                cv2.destroyAllWindows()
                return detected_criminal
            else:
                print(f"[NO MATCH] Face detected, but not matched. (Confidence: {conf:.2f})")

        # Show webcam window
        cv2.imshow("Face Verification - Press 'q' to cancel", frame)

        # Manual quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Manual quit.")
            break

        # Timeout (default 10 seconds)
        if time.time() - start_time > timeout:
            print("[INFO] Face recognition timeout.")
            break

    cam.release()
    cv2.destroyAllWindows()
    return None