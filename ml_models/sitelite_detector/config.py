import os

DEFAULT_WEIGHTS_PATH = os.environ.get('UNET_WEIGHTS', 'data/models/unet_roads.pth')
DEVICE = os.environ.get('UNET_DEVICE', 'cuda')
INPUT_SIZE = (512, 512)
NUM_CLASSES = 7
CLASSES = [
    'road_lane',
    'sidewalk',
    'parking_spot',
    'green_zone',
    'bus_stop',
    'building',
    'bike_lane'
]
CLASS_COLORS = [
    (128, 64, 128),
    (244, 35, 232),
    (70, 70, 70),
    (107, 142, 35),
    (0, 0, 142),
    (220, 20, 60),
    (119, 11, 32)
]