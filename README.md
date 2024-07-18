1. Create a venv and `pip install -r requirements.txt`
2. Run `build.sh` to clone and build a patched `llama-cli` where `--ignore-eos` actually IGNORES eos instead of just banning it
3. Edit `run.sh` tweak parameters as desired, `roleplay.txt` is default prompt modify or replace as desired
4. Run `run.sh` to run inference
5. Streamlit app will open when it's ready