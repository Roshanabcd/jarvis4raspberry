# JARVIS OS — Google Colab OmniVoice Setup Guide

This guide describes how to configure and run the high-performance OmniVoice speech synthesis engine on Google Colab GPU runtimes (e.g. Nvidia Tesla T4 / A100) and link it automatically with JARVIS OS on your Raspberry Pi 5.

---

## 1. Prerequisites
- A Google account with access to [Google Colab](https://colab.research.google.com/) (free tier Tesla T4 is fully supported).
- The modified notebook: `/home/roshan/Downloads/Super_Eleven_Lab_Lite_2_1.ipynb`.
- Your reference voice sample: `/home/roshan/Downloads/myvoice.mp3`.

---

## 2. Notebook Structure & Cells

The notebook `Super_Eleven_Lab_Lite_2_1.ipynb` is structured into 3 cells:

### Cell 1: Environment & Dependencies
Installs PyTorch, torchaudio, Gradio, and huggingface_hub:
```bash
!pip install -q gradio torchaudio soundfile huggingface_hub
```

### Cell 2: Model Weights Download & Initialization
Loads the OmniVoice multilingual diffusion model onto CUDA:
```python
import torch
device = "cuda:0" if torch.cuda.is_available() else "cpu"
# Downloads weights and prepares diffusion pipelines
```

### Cell 3: Premium Customized UI & Automatic Registration
Launches the Gradio interface with `prevent_thread_lock=True`, extracts the public share URL, and registers with JARVIS OS:
```python
app, local_url, share_url = demo.launch(
    share=True,
    debug=True,
    prevent_thread_lock=True,
    theme=gr.themes.Soft(primary_hue="violet", secondary_hue="cyan"),
    css=css
)
```

---

## 3. How to Launch & Connect

### Method A: Web Dashboard Quick Connect (Recommended)
1. In Colab, run all cells (**Runtime → Run all**).
2. Wait for Cell 3 to output:
   ```
   * Running on public URL: https://xxxx.gradio.live
   ```
3. Open the JARVIS OS Web Dashboard at `http://localhost:8000/`.
4. Navigate to **Voice Center**.
5. In the **Google Colab OmniVoice Server** panel, paste the URL into the input field and click **🔗 Connect & Register**.
6. JARVIS verifies the schema, saves the URL to `data/omnivoice_state.json`, and immediately switches to cloned voice mode.

### Method B: Fully Automatic Registration via Callback
If your Raspberry Pi has a reachable hostname, local network IP, or Cloudflare/ngrok tunnel, you can configure automatic registration inside the Colab environment:
```python
import os
os.environ["JARVIS_CALLBACK_URL"] = "https://your-jarvis-tunnel.trycloudflare.com"
```
When Cell 3 launches, it will automatically send a `POST` request to `/api/integrations/omnivoice/register` with the secret token, requiring zero manual copy-pasting.

### Method C: Colab CLI Execution from Raspberry Pi
You can launch or inspect Colab directly from your Raspberry Pi terminal:
```bash
colab exec -s testColab -f /home/roshan/Downloads/Super_Eleven_Lab_Lite_2_1.ipynb
```

---

## 4. Verification Checklist
- [x] Colab runtime shows GPU: `Tesla T4 (15.6 GB)`.
- [x] Gradio public link is active and accessible via HTTPS.
- [x] `POST /api/integrations/omnivoice/register` returns HTTP 200 with status `"ready"`.
- [x] Dashboard Voice Center badge displays `🟢 CLONED VOICE READY`.
- [x] Test synthesis returns `is_cloned: true` and `provider: "omnivoice_clone"`.
