"""
OmniVoice Voice Cloner for JARVIS OS.
Production Hugging Face Space application with ZeroGPU acceleration.
Exposes both an interactive Gradio web UI and a dedicated `/clone_voice` API endpoint.
"""

import os
import tempfile
import torch
import torchaudio
import gradio as gr

# Support Hugging Face Spaces ZeroGPU if available
try:
    import spaces
    gpu_decorator = spaces.GPU
except ImportError:
    gpu_decorator = lambda fn: fn

from omnivoice import OmniVoice

device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
dtype = torch.float16 if torch.cuda.is_available() else torch.float32

print(f"Loading OmniVoice model on device={device}, dtype={dtype}...")
model = OmniVoice.from_pretrained('k2-fsa/OmniVoice', device_map=device, dtype=dtype)
print("OmniVoice Model loaded successfully!")

NONVERBAL_TAGS = [
    '[laughter]', '[sigh]', '[sniff]', '[question-en]',
    '[surprise-ah]', '[dissatisfaction-hnn]', '[confirmation-en]'
]

DESIGN_PRESETS = {
    'Custom (type your own)': '',
    'Female, British accent': 'female, british accent',
    'Male, American accent': 'male, american accent',
    'Female, high pitch, young': 'female, high pitch, young adult',
    'Male, deep, elderly': 'male, very low pitch, elderly',
    'Female, whisper': 'female, whisper',
    'Male, Australian accent': 'male, australian accent',
    'Female, Indian accent': 'female, indian accent',
    'Male, fast, energetic': 'male, high pitch, young adult',
}

EXAMPLE_TEXTS = [
    'Hello! OmniVoice supports over 600 languages with state-of-the-art voice cloning.',
    '[laughter] You really got me. I did not see that coming at all.',
    'Breaking news: scientists have made a remarkable discovery.',
    'JARVIS OS voice cloning subsystem online and operational.',
]


@gpu_decorator
def synthesize_core(text, ref_audio=None, ref_text="", instruct="", num_steps=32, speed=1.0):
    """Core synthesis method with GPU acceleration."""
    if not text or not text.strip():
        return None, "Empty text prompt"

    kwargs = dict(
        text=text.strip(),
        num_step=max(8, min(64, int(num_steps))),
        speed=max(0.5, min(2.0, float(speed)))
    )

    if ref_audio is not None:
        kwargs['ref_audio'] = ref_audio
        if ref_text and ref_text.strip():
            kwargs['ref_text'] = ref_text.strip()
    elif instruct and instruct.strip():
        kwargs['instruct'] = instruct.strip()

    audio = model.generate(**kwargs)
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    audio_tensor = audio[0] if isinstance(audio[0], torch.Tensor) else torch.tensor(audio[0])
    if audio_tensor.dim() == 1:
        audio_tensor = audio_tensor.unsqueeze(0)
    torchaudio.save(tmp.name, audio_tensor.cpu(), 24000)
    duration = audio[0].shape[-1] / 24000
    return tmp.name, f"Synthesized {duration:.2f}s audio"


@gpu_decorator
def clone_voice_api(text: str, ref_audio, ref_text: str = "", num_steps: int = 32, speed: float = 1.0):
    """
    Dedicated programmatic endpoint for JARVIS OS.
    Accepts text and reference audio directly.
    """
    if not text or not text.strip():
        return None, "Error: Text cannot be empty"
    try:
        audio_path, status_msg = synthesize_core(
            text=text,
            ref_audio=ref_audio,
            ref_text=ref_text,
            num_steps=num_steps,
            speed=speed
        )
        return audio_path, status_msg
    except Exception as exc:
        return None, f"Error during synthesis: {exc}"


def generate_ui(text, mode, ref_audio, ref_text, design_preset, custom_instruct, num_steps, speed):
    """Handler for the interactive Gradio UI."""
    if not text or not text.strip():
        return None, "Please enter some text."
    try:
        instruct = ""
        actual_ref_audio = None
        if mode == 'Voice Cloning':
            if ref_audio is None:
                return None, "Please upload a reference audio file."
            actual_ref_audio = ref_audio
        elif mode == 'Voice Design':
            instruct = custom_instruct.strip() if design_preset == 'Custom (type your own)' else DESIGN_PRESETS.get(design_preset, "")
            if not instruct:
                return None, "Please enter a voice design instruction."

        audio_path, status_msg = synthesize_core(
            text=text,
            ref_audio=actual_ref_audio,
            ref_text=ref_text if mode == 'Voice Cloning' else "",
            instruct=instruct,
            num_steps=num_steps,
            speed=speed
        )
        return audio_path, f"{status_msg} | Mode: {mode}"
    except Exception as exc:
        return None, f"Error: {exc}"


def update_mode(mode):
    return (
        gr.update(visible=mode == 'Voice Cloning'),
        gr.update(visible=mode == 'Voice Cloning'),
        gr.update(visible=mode == 'Voice Design'),
        gr.update(visible=mode == 'Voice Design')
    )


def update_preset(preset):
    return gr.update(visible=preset == 'Custom (type your own)')


def insert_tag(text, tag):
    return (text + " " + tag).strip()


css = """
:root {
    --primary: #7c3aed;
    --accent: #22d3ee;
}
#header {
    text-align: center;
    padding: 20px 0;
    background: linear-gradient(135deg, #1e1b4b, #312e81);
    border-radius: 20px;
    margin-bottom: 20px;
    box-shadow: 0 15px 40px rgba(124, 58, 237, 0.4);
}
.gen-btn {
    background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
    color: white !important;
    border-radius: 50px !important;
    padding: 16px 40px !important;
    font-weight: 700;
}
"""

with gr.Blocks(title="JARVIS OS - OmniVoice Cloner", theme=gr.themes.Soft(primary_hue="violet", secondary_hue="cyan"), css=css) as demo:
    gr.HTML("""
    <div id="header">
        <h1 style="font-size: 2.6em; margin: 0 0 8px 0; background: linear-gradient(90deg, #c4b5fd, #67e8f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            JARVIS OS • OmniVoice Cloner
        </h1>
        <p style="margin: 0; opacity: 0.9; color: #e0e7ff;">Permanent Cloud Voice Synthesis & Cloning Backend</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            text_input = gr.Textbox(label="Text to speak", placeholder="Enter your text here...", lines=4)

            gr.Markdown("**Non-verbal tags:**")
            with gr.Row():
                for tag in NONVERBAL_TAGS:
                    btn = gr.Button(tag, size="sm")
                    btn.click(insert_tag, inputs=[text_input, gr.State(tag)], outputs=text_input)

            mode_radio = gr.Radio(['Auto Voice', 'Voice Cloning', 'Voice Design'], value='Voice Cloning', label="Generation Mode")

            ref_audio = gr.Audio(label="Reference Audio", type="filepath", visible=True)
            ref_text = gr.Textbox(label="Reference Transcript (optional)", visible=True)
            design_preset = gr.Dropdown(choices=list(DESIGN_PRESETS.keys()), value="Female, British accent", label="Voice Style", visible=False)
            custom_instruct = gr.Textbox(label="Custom Voice Instruction", visible=False)

            mode_radio.change(update_mode, mode_radio, [ref_audio, ref_text, design_preset, custom_instruct])
            design_preset.change(update_preset, design_preset, custom_instruct)

            with gr.Row():
                steps = gr.Slider(8, 64, 32, step=8, label="Diffusion Steps")
                speed = gr.Slider(0.5, 2.0, 1.0, step=0.1, label="Speed")

            gen_btn = gr.Button("🚀 Generate Speech", elem_classes="gen-btn", variant="primary")
            status = gr.Markdown()

        with gr.Column(scale=2):
            audio_out = gr.Audio(label="Output Audio", type="filepath")

    gen_btn.click(
        generate_ui,
        [text_input, mode_radio, ref_audio, ref_text, design_preset, custom_instruct, steps, speed],
        [audio_out, status],
        api_name="generate"
    )

    # Dedicated programmatic API endpoint for JARVIS OS background daemon
    api_text = gr.Textbox(visible=False)
    api_ref = gr.Audio(type="filepath", visible=False)
    api_ref_txt = gr.Textbox(visible=False)
    api_steps = gr.Number(value=32, visible=False)
    api_spd = gr.Number(value=1.0, visible=False)
    api_audio_out = gr.Audio(visible=False)
    api_status_out = gr.Textbox(visible=False)

    api_btn = gr.Button(visible=False)
    api_btn.click(
        clone_voice_api,
        inputs=[api_text, api_ref, api_ref_txt, api_steps, api_spd],
        outputs=[api_audio_out, api_status_out],
        api_name="clone_voice"
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
