from datetime import datetime
import cv2
import pickle
import os
import time
from pymongo import MongoClient

# MongoDB connection (optional - can be extended to log detections)
client = MongoClient('mongodb://localhost:27017/')
db = client['criminal_detection_system']

def preprocess_face_for_recognition(face):
    face_resized = cv2.resize(face, (200, 200))
    face_eq = cv2.equalizeHist(face_resized)
    return face_eq

def recognize_face_from_webcam(timeout=10):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    model_path = os.path.join(os.path.dirname(__file__), "criminal_trained_model.yml")
    
    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found: {model_path}")
        return "ModelNotFound"
    
    recognizer.read(model_path)

    labels_path = os.path.join(os.path.dirname(__file__), 'trainer', 'labels.pickle')
    if not os.path.exists(labels_path):
        print(f"[ERROR] Labels file not found: {labels_path}")
        return "LabelsNotFound"

    with open(labels_path, "rb") as f:
        labels = pickle.load(f)
        labels = {v: k for k, v in labels.items()}

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cam = cv2.VideoCapture(0)

    detected_criminal = None
    start_time = time.time()
    
    # Recommended threshold for rejecting bad matches
    REJECTION_THRESHOLD = 55

    while True:
        ret, frame = cam.read()
        if not ret:
            print("[ERROR] Failed to grab frame")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))

        for (x, y, w, h) in faces:
            roi = gray[y:y+h, x:x+w]
            processed_face = preprocess_face_for_recognition(roi)

            id_, conf = recognizer.predict(processed_face)
            print(f"[INFO] Detected face - Confidence score: {conf:.2f}")

            if conf < REJECTION_THRESHOLD:
                name = labels.get(id_, "Unknown")

                print(f"[MATCH] Recognized: {name} (Confidence: {conf:.2f})")
                detected_criminal = name

                # Save matched frame
                detected_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'detected_criminals')
                os.makedirs(detected_dir, exist_ok=True)

                existing_files = [f for f in os.listdir(detected_dir) if f.startswith('detected_') and f.endswith('.jpg')]
                try:
                    next_num = max([int(f.split('_')[1].split('.')[0]) for f in existing_files]) + 1
                except:
                    next_num = 1

                filename = f"detected_{next_num}.jpg"
                filepath = os.path.join('static', 'detected_criminals', filename).replace('\\', '/')
                cv2.imwrite(os.path.join(detected_dir, filename), frame)

                print(f"[INFO] Saved detected image to: {filepath}")
                cam.release()
                cv2.destroyAllWindows()
                return detected_criminal
            else:
                print(f"[REJECTED] Face not recognized (Confidence: {conf:.2f})")

        cv2.imshow("Face Verification - Press 'q' to cancel", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Manual quit.")
            break

        if time.time() - start_time > timeout:
            print("[INFO] Face recognition timeout.")
            break

    cam.release()
    cv2.destroyAllWindows()
    return None
