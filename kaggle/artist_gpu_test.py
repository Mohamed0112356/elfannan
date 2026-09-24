import os, sys, subprocess
from pathlib import Path

print("=== ElFannan / Kaggle GPU test ===")
print("Python:", sys.version)
print("Working dir:", Path.cwd())
print("HF_HOME:", os.getenv("HF_HOME"))
try:
    import torch
    print("Torch:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}:", torch.cuda.get_device_name(i))
            print(f"VRAM {i}:", round(torch.cuda.get_device_properties(i).total_memory/1024**3, 2), "GB")
except Exception as e:
    print("Torch check failed:", repr(e))

print("\nNext: clone the ElFannan GitHub repo into /kaggle/working/ElFannan")
