# الفنان (ElFannan)

AI Artist Engine: a small orchestration layer for building a persistent virtual music artist.

## Architecture
- `src/elfannan/`: core orchestration
- `artists/`: artist bibles and character assets
- `engines/ace-step/`: music generation engine (separate environment)
- `engines/rvc/`: voice conversion engine (separate environment)
- `data/`: local inputs and generated outputs
- `kaggle/`: GPU test/push files

## Rule
Keep the core environment light. Do **not** install ACE-Step or RVC dependencies into the core `.venv`; each engine gets its own environment.
