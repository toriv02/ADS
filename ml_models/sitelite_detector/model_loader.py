import os
import torch
from .unet_model import UNet
from .config import DEFAULT_WEIGHTS_PATH, NUM_CLASSES, DEVICE

def download_pretrained_weights(save_path=None):
    if save_path is None:
        save_path = DEFAULT_WEIGHTS_PATH
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    if not os.path.exists(save_path):
        url = "https://github.com/milesial/Pytorch-UNet/releases/download/v3.0/unet_carvana_scale0.5_epoch2.pth"
        import urllib.request
        urllib.request.urlretrieve(url, save_path)
    return save_path

def load_unet_model(weights_path=None, device=None):
    if weights_path is None:
        weights_path = DEFAULT_WEIGHTS_PATH
    if not os.path.exists(weights_path):
        weights_path = download_pretrained_weights(weights_path)
    device = device or DEVICE
    model = UNet(n_channels=3, n_classes=NUM_CLASSES)
    state_dict = torch.load(weights_path, map_location=device)
    if 'state_dict' in state_dict:
        state_dict = state_dict['state_dict']
    model.load_state_dict(state_dict, strict=False)
    model.to(device)
    model.eval()
    return model