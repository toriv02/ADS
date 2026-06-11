import os
import random
import torch
import numpy as np
from PIL import Image
from omegaconf import OmegaConf
from accelerate.utils import set_seed
from diffbir.model.cldm import ControlLDM
from diffbir.model.swinir import SwinIR
from diffbir.pipeline import SwinIRPipeline
from diffbir.utils.common import instantiate_from_config, load_model_from_url
from diffbir.utils.caption import EmptyCaptioner, LLaVACaptioner, RAMCaptioner
from diffbir.inference.pretrained_models import MODELS

CONFIG_DIR = os.environ.get("DIFFBIR_CONFIG_DIR", "configs")

class DiffBIRWrapper:
    def __init__(self, device="cuda", precision="fp16", captioner_type="none", llava_bit="4"):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.precision = precision
        self.captioner_type = captioner_type
        self.llava_bit = llava_bit
        torch.set_grad_enabled(False)
        self._load_models()
        self._load_captioner()

    def _load_models(self):
        swinir_cfg = OmegaConf.load(os.path.join(CONFIG_DIR, "inference/swinir.yaml"))
        self.swinir = instantiate_from_config(swinir_cfg)
        self.swinir.load_state_dict(load_model_from_url(MODELS["swinir_realesrgan"]))
        self.swinir.eval().to(self.device)

        face_cfg = OmegaConf.load(os.path.join(CONFIG_DIR, "inference/swinir.yaml"))
        self.face_swinir = instantiate_from_config(face_cfg)
        self.face_swinir.load_state_dict(load_model_from_url(MODELS["swinir_face"]))
        self.face_swinir.eval().to(self.device)

        cldm_cfg = OmegaConf.load(os.path.join(CONFIG_DIR, "inference/cldm.yaml"))
        self.cldm = instantiate_from_config(cldm_cfg)
        sd_weight = load_model_from_url(MODELS["sd_v2.1_zsnr"])
        self.cldm.load_pretrained_sd(sd_weight)
        control_weight = load_model_from_url(MODELS["v2.1"])
        self.cldm.load_controlnet_from_ckpt(control_weight)
        self.cldm.eval().to(self.device)

        cast_type = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}[self.precision]
        self.cldm.cast_dtype(cast_type)

        diffusion_cfg = OmegaConf.load(os.path.join(CONFIG_DIR, "inference/diffusion_v2.1.yaml"))
        self.diffusion = instantiate_from_config(diffusion_cfg)
        self.diffusion.to(self.device)

    def _load_captioner(self):
        if self.captioner_type == "none":
            self.captioner = EmptyCaptioner(self.device)
        elif self.captioner_type == "llava":
            self.captioner = LLaVACaptioner(self.device, self.llava_bit)
        elif self.captioner_type == "ram":
            self.captioner = RAMCaptioner(self.device)
        else:
            raise ValueError(f"Unknown captioner type: {self.captioner_type}")

    def enhance(self,
                image_path,
                task="sr",
                upscale=4,
                cleaner_tiled=False,
                cleaner_tile_size=256,
                vae_encoder_tiled=False,
                vae_encoder_tile_size=256,
                vae_decoder_tiled=False,
                vae_decoder_tile_size=256,
                cldm_tiled=True,
                cldm_tile_size=512,
                positive_prompt="Cinematic, High Contrast, highly detailed, taken using a Canon EOS R camera, hyper detailed photo - realistic maximum detail, 32k, Color Grading, ultra HD, extreme meticulous detailing, skin pore detailing, hyper sharpness, perfect without deformations.",
                negative_prompt="painting, oil painting, illustration, drawing, art, sketch, oil painting, cartoon, CG Style, 3D render, unreal engine, blurring, dirty, messy, worst quality, low quality, frames, watermark, signature, jpeg artifacts, deformed, lowres, over-smooth.",
                cfg_scale=8,
                strength=1.0,
                noise_aug=0,
                steps=10,
                sampler_type="edm_dpm++_3m_sde",
                s_churn=0,
                s_tmin=0,
                s_tmax=300,
                s_noise=1.0,
                order=1,
                seed=231):
        if seed == -1:
            seed = random.randint(0, 2147483647)
        set_seed(seed)

        lq = Image.open(image_path).convert("RGB")

        caption = self.captioner(lq)
        pos_prompt = ", ".join([text for text in [caption, positive_prompt] if text])
        neg_prompt = negative_prompt

        out_w, out_h = tuple(int(x * upscale) for x in lq.size)
        lq = lq.resize((out_w, out_h), Image.BICUBIC)
        lq = np.array(lq)

        if task == "sr":
            cleaner = self.swinir
        else:
            cleaner = self.face_swinir

        pipeline = SwinIRPipeline(cleaner, self.cldm, self.diffusion, None, self.device)

        sample = pipeline.run(
            lq[None],
            steps,
            strength,
            cleaner_tiled,
            cleaner_tile_size,
            cleaner_tile_size // 2,
            vae_encoder_tiled,
            vae_encoder_tile_size,
            vae_decoder_tiled,
            vae_decoder_tile_size,
            cldm_tiled,
            cldm_tile_size,
            cldm_tile_size // 2,
            pos_prompt,
            neg_prompt,
            cfg_scale,
            "noise",
            sampler_type,
            noise_aug,
            False,
            s_churn,
            s_tmin,
            s_tmax,
            s_noise,
            1,
            order,
        )[0]

        result = Image.fromarray(sample)
        return result

_enhancer = None

def get_enhancer():
    global _enhancer
    if _enhancer is None:
        _enhancer = DiffBIRWrapper()
    return _enhancer

def enhance_image(image_path, quality='balanced'):
    enhancer = get_enhancer()
    steps_map = {
        'fast': 10,
        'balanced': 25,
        'high': 50
    }
    steps = steps_map.get(quality, 25)
    result = enhancer.enhance(image_path, steps=steps)
    out_path = image_path.replace('.', '_enhanced.')
    result.save(out_path)
    return out_path