# Kaggle GPU workflow

Source of truth: GitHub repository.

Kaggle notebook should clone the repo, install only the engine needed for the current experiment, run the test, and save outputs/checkpoints to Kaggle Dataset or download them back locally.

Do not store API keys, `.env`, or private credentials in GitHub or notebook code.
