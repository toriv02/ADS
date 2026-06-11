import torch
import torchvision.transforms as T
from PIL import Image
import numpy as np
from .model_loader import load_unet_model
from .postprocess import extract_objects
from .config import DEVICE, INPUT_SIZE, NUM_CLASSES

class UNetSegmenter:
    def __init__(self, weights_path=None, device=None):
        self.device = device or DEVICE
        self.model = load_unet_model(weights_path, self.device)
        self.input_size = INPUT_SIZE
        self.transform = T.Compose([
            T.Resize(INPUT_SIZE),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def segment(self, image_path, return_mask=False):
        img = Image.open(image_path).convert('RGB')
        orig_size = img.size[::-1]
        input_tensor = self.transform(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            output = self.model(input_tensor)
            pred = torch.argmax(output, dim=1).squeeze(0).cpu().numpy()
        pred = pred.astype(np.uint8)
        if pred.shape != orig_size:
            pred = cv2.resize(pred, (orig_size[1], orig_size[0]), interpolation=cv2.INTER_NEAREST)
        objects = extract_objects(pred, orig_size)
        summary = self._aggregate_results(objects)
        result = {'objects': objects, 'summary': summary}
        if return_mask:
            result['mask'] = pred
        return result

    def _aggregate_results(self, objects):
        summary = {
            'road_lane': {'count': 0, 'total_area': 0},
            'sidewalk': {'count': 0, 'total_area': 0},
            'parking_spot': {'count': 0, 'total_area': 0},
            'green_zone': {'count': 0, 'total_area': 0},
            'bus_stop': {'count': 0, 'total_area': 0},
            'building': {'count': 0, 'total_area': 0},
            'bike_lane': {'count': 0, 'total_area': 0}
        }
        for obj in objects:
            obj_type = obj['type']
            summary[obj_type]['count'] += 1
            summary[obj_type]['total_area'] += obj['area']
        return summary

def segment_image(image_path, weights_path=None):
    segmenter = UNetSegmenter(weights_path)
    return segmenter.segment(image_path)