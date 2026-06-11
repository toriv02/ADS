import os

def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_output_path(input_path, suffix='_enhanced', ext='.jpg'):
    base, _ = os.path.splitext(input_path)
    return f"{base}{suffix}{ext}"

def list_images_in_directory(directory, extensions=('.jpg', '.jpeg', '.png')):
    return [os.path.join(directory, f) for f in os.listdir(directory)
            if f.lower().endswith(extensions)]