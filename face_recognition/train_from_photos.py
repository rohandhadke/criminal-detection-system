import cv2
import os
import numpy as np
from PIL import Image
import pickle

def preprocess_face(face):
    """Resize and equalize histogram of the face for consistency."""
    face_resized = cv2.resize(face, (200, 200))
    face_eq = cv2.equalizeHist(face_resized)
    return face_eq

def augment_face(face):
    """Augment face data by flipping and rotating."""
    augmented = [face]
    flipped = cv2.flip(face, 1)
    augmented.append(flipped)
    rotated = cv2.rotate(face, cv2.ROTATE_90_CLOCKWISE)
    augmented.append(rotated)
    return augmented

def train():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.normpath(os.path.join(base_dir, "..", "static", "photos"))

    # Check if image directory exists
    if not os.path.exists(path):
        print(f"[ERROR] Directory '{path}' not found.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    image_paths = [os.path.join(path, f) for f in os.listdir(path)
                   if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    print(f"[INFO] Found {len(image_paths)} image files.")

    face_samples = []
    ids = []
    labels_dict = {}
    current_id = 0

    for image_path in image_paths:
        print(f"[INFO] Processing: {image_path}")
        try:
            img = Image.open(image_path).convert('L')  # Convert to grayscale
        except Exception as e:
            print(f"[WARNING] Could not open {image_path}: {e}")
            continue

        img_np = np.array(img, 'uint8')

        # Better detection parameters
        faces = detector.detectMultiScale(
            img_np,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        filename = os.path.basename(image_path)
        label = filename.split("_")[0]

        if label not in labels_dict:
            labels_dict[label] = current_id
            current_id += 1
        id_ = labels_dict[label]

        if len(faces) == 0:
            print(f"[WARNING] No face detected in {image_path}")
            continue

        for (x, y, w, h) in faces:
            face = img_np[y:y+h, x:x+w]
            face = preprocess_face(face)
            augmented_faces = augment_face(face)
            for aug_face in augmented_faces:
                face_samples.append(aug_face)
                ids.append(id_)

    if len(face_samples) < 2:
        print("[ERROR] Not enough face samples detected for training. At least 2 are required.")
        return

    print(f"[INFO] Training on {len(face_samples)} face samples...")
    recognizer.train(face_samples, np.array(ids))
    recognizer.save("criminal_trained_model.yml")
    print("[INFO] Training complete. Model saved as 'criminal_trained_model.yml'.")

    # Save label mappings
    trainer_dir = "trainer"
    if not os.path.exists(trainer_dir):
        os.makedirs(trainer_dir)

    with open(os.path.join(trainer_dir, "labels.pickle"), "wb") as f:
        pickle.dump(labels_dict, f)
    print("[INFO] Labels saved to 'trainer/labels.pickle'.")

if __name__ == "__main__":
    train()
