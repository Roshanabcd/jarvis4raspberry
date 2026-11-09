# JARVIS OS — Phase 1 AI Provider Status & Benchmark Analysis

## 1. Provider Ecosystem & API Verification

JARVIS OS integrates a multi-provider AI architecture centered on the local Ollama daemon running on Raspberry Pi 5.

- **Primary Server:** `http://127.0.0.1:11434` (Ollama 0.x / llama-server backend)
- **Host Hardware:** Raspberry Pi 5 (Quad-core ARM Cortex-A76 @ 2.4 GHz, 8 GB LPDDR4X)
- **Active Provider:** `ollama`
- **Default Model:** `llama3.2:1b`
- **Alternative Local Model:** `qwen3.5:4b`
- **Cloud Adapters Available:** Google Gemini (`gemini-2.0-flash`), OpenAI (`gpt-4o-mini`), Anthropic Claude, NVIDIA NIM.

---

## 2. Local Model Benchmark Comparison

Measurements recorded on live Raspberry Pi 5 hardware (Debian 13 Trixie, kernel 6.18.60-1+rpt1 aarch64):

| Metric | `llama3.2:1b` (Default) | `qwen3.5:4b` (Optional) | Analysis & Impact |
|---|---|---|---|
| **Parameter Size** | 1.23 Billion | 4.70 Billion | Llama is 3.8x smaller; lighter compute footprint |
| **Quantization Format** | GGUF Q8_0 | GGUF Q4_K_M | Llama retains high precision at Q8 |
| **Disk Image Size** | 1.32 GB | 3.39 GB | Both stored in `/usr/share/ollama/.ollama` |
| **RAM Footprint (Resident)** | ~1.80 GB | ~3.66 GB | Llama leaves ~6 GB free RAM for OS & services |
| **Cold Startup Latency** | 47.74 s | 154.01 s | Qwen requires >2.5 minutes to load into memory |
| **Warm Time-To-First-Token** | **1.24 s** | 18.50 s | Llama provides near-instantaneous interaction |
| **Average Generation Speed** | **6.8 – 8.85 tok/s** | 1.2 – 2.1 tok/s | Llama is ~4x faster on Cortex-A76 CPU |
| **Max Context Configured** | 4,096 tokens | 4,096 tokens | Balanced for low memory pressure |
| **Output Token Limit** | 1,024 – 2,048 tokens | 1,024 – 2,048 tokens | Eliminates arbitrary answer truncation |

### Architectural Decision:
`llama3.2:1b` is selected as the primary default model. It delivers excellent conversational coherence, valid Python code synthesis, and sub-2-second responsiveness while preserving ample RAM for PipeWire audio buffers, computer vision processing, and background services. `qwen3.5:4b` is retained and dynamically selectable via `POST /api/chat/model`.

---

## 3. Provider Routing & Deception Elimination

Previous releases displayed a deceptive fallback when Ollama was unreachable:
> *"I understand you said: hello jarvis. I'm running in local intelligence mode (no LLM connected)..."*

This was removed. The new provider routing invariant guarantees:
1. **Direct Connection:** When Ollama is active, requests route directly to the active model.
2. **Honest Failure Reporting:** If Ollama is stopped or unreachable, the system returns a truthful status:
   `⚠️ AI Provider Error: Ollama server is unreachable at http://127.0.0.1:11434...` with `status: "failed"` and `provider: "error"`.
3. **No Fabricated Output:** The assistant never pretends that local rule templates are AI outputs.
