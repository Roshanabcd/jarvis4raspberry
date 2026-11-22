# JARVIS OS: Avatar Asset Specification & Registry

Target: Phase 5 (Digital Human Avatar) & SPEC.md Section 4

## 1. Status: Real Avatar Model Files Missing (Stop Condition 2)

Per `AGENTS.md` Stop Condition 2 and `docs/jarvis-ui/PLAN.md` Phase 5 Gate:
- Real 3D avatar files (`.vrm`, `.glb`) are not present in the repository.
- No copyrighted or unlicensed 3D character models may be downloaded without explicit operator permission.

## 2. Supported Avatar Renderers

### Renderer A: 2D Digital Human SVG Vector Graphics (`Svg2D`)
- **Source:** High-fidelity vector graphics extracted and ported from `docs/jarvis-ui/references/jarvis_os_futuristic_ai_interface.tsx`.
- **Characters:**
  - **ARIA (Female):** Adult female-presenting digital human with futuristic holographic suit, cyan/purple halo rings, and expressiveness.
  - **ATLAS (Male):** Adult male-presenting digital human with futuristic cybernetic suit and glowing accents.
- **Capabilities:**
  - 9 visual states: `idle`, `listening`, `thinking`, `speaking`, `happy`, `concerned`, `error`, `offline`, `muted`.
  - 5 mouth viseme shapes: `closed`, `smile`, `small`, `mid`, `wide`.
  - Natural periodic eye blinking (140ms blinks every 2.4–5.6 seconds).
  - Micro-gaze tracking and subtle head breathing.
  - Rotating holographic scanline HUD rings.
  - Performance: 60 FPS, 0 external download dependencies, operates smoothly on Raspberry Pi 5 and low-power laptops.
- **License:** Internal workspace reference prototype (CC0 / project asset).

### Renderer B: 3D VRM Digital Human (`Vrm3D`)
- **Target Format:** VRM 1.0 (glTF 2.0 based humanoid avatar format).
- **Engine:** Three.js + `@pixiv/three-vrm`.
- **Target Specifications:**
  - File Paths: `apps/dashboard/futuristic/assets/avatars/aria.vrm`, `apps/dashboard/futuristic/assets/avatars/atlas.vrm`.
  - Polygon Budget: < 35,000 triangles (recommended for integrated AMD Radeon / Raspberry Pi).
  - Blendshapes Required:
    - Eye blinks: `blink`, `blinkLeft`, `blinkRight`.
    - Visemes: `aa`, `ih`, `ou`, `ee`, `oh`.
    - Expressions: `happy`, `surprised`, `relaxed`, `neutral`.
  - Spring Bones: Hair and subtle suit accents only.
  - File Size: < 25 MB per model.
  - Status: Awaiting user-supplied model files or operator approval.

## 3. Fallback Hierarchy
1. If `aria.vrm` / `atlas.vrm` is placed in assets directory and WebGL2 is available → use `Vrm3D`.
2. If VRM files are absent or WebGL fails → seamlessly fall back to `Svg2D` (ARIA / ATLAS).
3. If low-power / reduced-motion mode is active → freeze rotating HUD rings and reduce micro-movements while preserving speaking mouth shapes and blinking.
