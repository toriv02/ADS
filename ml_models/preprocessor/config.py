import os
import torch

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

DIFFBIR_WEIGHTS_PATH = os.environ.get('DIFFBIR_WEIGHTS', 'data/models/diffbir/diffbir.pth')
DIFFBIR_CONFIG_DIR = os.environ.get('DIFFBIR_CONFIG_DIR', 'configs')

DEFAULT_QUALITY = 'balanced'

MIN_ENHANCE_SIZE = (320, 240)