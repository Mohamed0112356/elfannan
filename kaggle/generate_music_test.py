from pathlib import Path
import os

# Kaggle/Jupyter sets MPLBACKEND to matplotlib_inline. ACE-Step runs as a
# standalone process, so force a non-interactive backend before matplotlib
# is imported by lightning/torchmetrics.
os.environ["MPLBACKEND"] = "Agg"
import shutil
import json
import time

# Kaggle runtime paths used by the existing notebook.
PROJECT_ROOT = Path("/kaggle/temp/ElFannan")
ACE_ROOT = Path("/kaggle/temp/ACE-Step-1.5")
CHECKPOINTS = PROJECT_ROOT / "models"

# ACE-Step 1.5 currently ignores the documented ACESTEP_DTYPE environment
# variable in its CUDA dtype-selection code. On T4 (pre-Ampere), the
# upstream fallback is FP16, which can produce NaN latents during lyrics
# generation. Patch that selector before importing acestep so the model is
# actually loaded in FP32.
ACESTEP_DTYPE = "float32"
os.environ["ACESTEP_DTYPE"] = ACESTEP_DTYPE


def patch_acestep_dtype() -> None:
    orchestrator = (
        ACE_ROOT
        / "acestep"
        / "core"
        / "generation"
        / "handler"
        / "init_service_orchestrator.py"
    )
    if not orchestrator.exists():
        raise FileNotFoundError(f"ACE-Step orchestrator not found: {orchestrator}")

    source = orchestrator.read_text(encoding="utf-8")

    # Make sure the orchestrator can read ACESTEP_DTYPE.
    if "import os" not in source.split("\n", 30):
        source = source.replace("import torch\n", "import os\nimport torch\n", 1)

    old_block = '''        elif resolved_device == "cuda":
            if gpu_config.cuda_supports_bfloat16():
                self.dtype = torch.bfloat16
            else:
                self.dtype = torch.float16
                logger.info(
                    "[initialize_service] Pre-Ampere CUDA detected: using float16 instead of bfloat16."
                )'''

    new_block = '''        elif resolved_device == "cuda":
            env_dtype = os.environ.get("ACESTEP_DTYPE", "").strip().lower()
            if env_dtype in ("float32", "float16", "bfloat16"):
                self.dtype = getattr(torch, env_dtype)
                logger.info(
                    f"[initialize_service] ACESTEP_DTYPE={env_dtype} override: "
                    f"using dtype={self.dtype}."
                )
            elif gpu_config.cuda_supports_bfloat16():
                self.dtype = torch.bfloat16
            else:
                self.dtype = torch.float16
                logger.info(
                    "[initialize_service] Pre-Ampere CUDA detected: using float16 instead of bfloat16."
                )'''

    if "ACESTEP_DTYPE={env_dtype} override" in source:
        print("[OK] ACE-Step FP32 dtype override already present.")
    elif old_block in source:
        orchestrator.write_text(source.replace(old_block, new_block, 1), encoding="utf-8")
        print("[OK] Patched ACE-Step CUDA dtype selector for ACESTEP_DTYPE.")
    else:
        raise RuntimeError(
            "Could not patch ACE-Step dtype selector safely. "
            "The upstream source layout has changed; refusing a blind edit."
        )

    verify = orchestrator.read_text(encoding="utf-8")
    if 'env_dtype = os.environ.get("ACESTEP_DTYPE", "").strip().lower()' not in verify:
        raise RuntimeError("FP32 patch verification failed.")

patch_acestep_dtype()

OUTPUT_DIR = Path("/kaggle/working/elfannan_output")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

os.environ["ACESTEP_CHECKPOINTS_DIR"] = str(CHECKPOINTS)
os.environ["ACESTEP_SAVE_MEMORY"] = "1"\nos.environ["ACESTEP_DTYPE"] = ACESTEP_DTYPE
os.environ["ACESTEP_DISABLE_TQDM"] = "1"

print("=" * 70)
print("ELFANNAN MUSIC GENERATION TEST")
print("=" * 70)
print(f"Project:      {PROJECT_ROOT}")
print(f"ACE-Step:     {ACE_ROOT}")
print(f"Checkpoints:  {CHECKPOINTS}")
print(f"Output:       {OUTPUT_DIR}")

if not ACE_ROOT.exists():
    raise FileNotFoundError(f"ACE-Step directory not found: {ACE_ROOT}")

if not CHECKPOINTS.exists():
    raise FileNotFoundError(f"Checkpoint directory not found: {CHECKPOINTS}")

for model_name in ["acestep-v15-turbo", "vae", "Qwen3-Embedding-0.6B"]:
    model_dir = CHECKPOINTS / model_name
    print(f"  {model_name}: {'OK' if model_dir.exists() else 'MISSING'}")

import torch

if not torch.cuda.is_available():
    raise RuntimeError("CUDA is not available in this Kaggle session.")

print()
print("GPU:", torch.cuda.get_device_name(0))
print("VRAM:", round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2), "GB")
torch.cuda.set_device(0)

# ACE-Step official Python inference API.
from acestep.handler import AceStepHandler
from acestep.inference import GenerationParams, GenerationConfig, generate_music

print()
print("Initializing ACE-Step Turbo...")
dit_handler = AceStepHandler()

status, ok = dit_handler.initialize_service(
    project_root=str(ACE_ROOT),
    config_path="acestep-v15-turbo",
    device="cuda",
    use_flash_attention=False,
    compile_model=False,
    offload_to_cpu=True,
    offload_dit_to_cpu=False,
)

print(status)
if not ok:
    raise RuntimeError(f"ACE-Step initialization failed:\n{status}")

# First milestone: one short original Arabic vocal track.
# We intentionally disable the 5Hz LM in this first test so we test
# the DiT generation path independently and reduce moving parts.
lyrics = """[Verse]
في بالي لحن جديد
يمشي معايا كل يوم
في قلبي حلم بعيد
وبكرة نكمل للنجوم

[Chorus]
تعالى نغني للحياة
ونسيب أثر من الذكريات"""

params = GenerationParams(
    task_type="text2music",
    caption=(
        "modern Egyptian Arabic pop song, warm male vocal, catchy melodic hook, "
        "clean modern production, soft synths, subtle darbuka, punchy bass, "
        "emotional but hopeful mood"
    ),
    lyrics=lyrics,
    instrumental=False,
    vocal_language="ar",
    bpm=104,
    keyscale="A minor",
    timesignature="4",
    duration=20.0,
    inference_steps=8,
    seed=424242,
    thinking=False,
    use_cot_metas=False,
    use_cot_caption=False,
    use_cot_language=False,
    shift=3.0,
)

config = GenerationConfig(
    batch_size=1,
    use_random_seed=False,
    seeds=[424242],
    audio_format="wav",
)

print()
print("Generating one 20-second WAV...")
started = time.time()

result = generate_music(
    dit_handler=dit_handler,
    llm_handler=None,
    params=params,
    config=config,
    save_dir=str(OUTPUT_DIR),
)

elapsed = time.time() - started
print(f"Generation time: {elapsed:.1f}s")

if not result.success:
    raise RuntimeError(
        "Music generation failed.\n"
        f"Status: {result.status_message}\n"
        f"Error:  {result.error}"
    )

if not result.audios:
    raise RuntimeError("Generation reported success but returned no audio files.")

source_path = Path(result.audios[0]["path"])
final_path = OUTPUT_DIR / "elfannan_test.wav"
shutil.copy2(source_path, final_path)

metadata = {
    "source_path": str(source_path),
    "final_path": str(final_path),
    "elapsed_seconds": round(elapsed, 2),
    "seed": 424242,
    "duration_requested": 20.0,
    "bpm": 104,
    "language": "ar",
    "model": "acestep-v15-turbo",
    "lm_used": False,
}

(OUTPUT_DIR / "elfannan_test.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print()
print("=" * 70)
print("SUCCESS")
print("=" * 70)
print("WAV:", final_path)
print("Size:", round(final_path.stat().st_size / 1024 / 1024, 2), "MB")
print("Metadata:", OUTPUT_DIR / "elfannan_test.json")
print()
print("Files in output:")
for p in sorted(OUTPUT_DIR.iterdir()):
    print(f"  {p.name}  ({p.stat().st_size / 1024 / 1024:.2f} MB)")
