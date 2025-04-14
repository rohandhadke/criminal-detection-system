import cv2
import os
import numpy as np
from PIL import Image
import pickle

def train():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.normpath(os.path.join(base_dir, "..", "static", "photos"))
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    image_paths = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    print(f"[INFO] Found {len(image_paths)} image files.")

    face_samples = []
    ids = []
    labels_dict = {}
    current_id = 0

    for image_path in image_paths:
        print(f"[INFO] Processing: {image_path}")
        img = Image.open(image_path).convert('L')  # grayscale
        img_np = np.array(img, 'uint8')
        faces = detector.detectMultiScale(img_np)

        filename = os.path.basename(image_path)
        label = filename.split("_")[0]  # get name before first underscore

        if label not in labels_dict:
            labels_dict[label] = current_id
            current_id += 1
        id_ = labels_dict[label]

        if len(faces) == 0:
            print(f"[WARNING] No face detected in {image_path}")
            continue

        for (x, y, w, h) in faces:
            face_samples.append(img_np[y:y+h, x:x+w])
            ids.append(id_)

    if len(face_samples) < 2:
        print("[ERROR] Not enough face samples detected for training. At least 2 are required.")
        return

    print(f"[INFO] Training on {len(face_samples)} face samples...")
    recognizer.train(face_samples, np.array(ids))
    recognizer.save("criminal_trained_model.yml")
    print("[INFO] Training complete. Model saved as 'criminal_trained_model.yml'.")

    # Save labels dictionary
    if not os.path.exists("trainer"):
        os.makedirs("trainer")

    with open("trainer/labels.pickle", "wb") as f:
        pickle.dump(labels_dict, f)
    print("[INFO] Labels saved to 'trainer/labels.pickle'.")

if __name__ == "__main__":
    train()
