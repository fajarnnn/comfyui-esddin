from huggingface_hub import hf_hub_download
import os
token=os.getenv("HF_TOKEN_APP")
print(f"TKN={token}")
repo="Esddin/venv"
out="/workspace/runpod-slim/ComfyUI/models/aesthetic"
for f in [
  "ava+logos-l14-linearMSE.pth",
  "ava+logos-l14-reluMSE.pth",
  "sac+logos+ava1-l14-linearMSE.pth",
  "chadscorer.pth",
]:
  p=hf_hub_download(repo_id=repo, filename=f, token=token, local_dir=out)
  print("OK:", p)
