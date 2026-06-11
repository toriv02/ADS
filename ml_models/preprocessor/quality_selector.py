def get_enhance_params(quality):
    params = {
        'fast': {
            'num_inference_steps': 10,
            'noise_level': 0.5,
            'd': 5,
            'sigma_color': 50,
            'sigma_space': 50,
        },
        'balanced': {
            'num_inference_steps': 25,
            'noise_level': 0.3,
            'd': 9,
            'sigma_color': 75,
            'sigma_space': 75,
        },
        'high': {
            'num_inference_steps': 50,
            'noise_level': 0.1,
            'd': 15,
            'sigma_color': 100,
            'sigma_space': 100,
        }
    }
    return params.get(quality, params['balanced'])