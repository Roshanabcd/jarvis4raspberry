import { useState } from "react";

interface UIElement {
  element_id: string;
  role: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export default function DashboardPage() {
  const [statusText, setStatusText] = useState("Ready to inspect local screen captures and UI bounding boxes.");
  const [elements, setElements] = useState<UIElement[]>([]);

  async function createSampleCapture() {
    const res = await fetch("/api/v1/vision/captures", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: "JARVIS Desktop Snapshot",
        source: "desktop_primary",
        width: 1280,
        height: 720,
        ocr_text: "Deploy Production | System Logs",
        elements: [
          { element_id: "btn_deploy", role: "button", label: "Deploy Production", text: "Deploy", x: 90, y: 120, width: 320, height: 90, confidence: 0.99 }
        ]
      })
    });
    const data = await res.json();
    setElements(data.elements || []);
    setStatusText(`Indexed capture ${data.capture_id} (${data.width}x${data.height}).`);
  }

  return (
    <div className="min-h-screen bg-jarvisBg text-[#F0F8FF] p-6">
      <h1 className="text-2xl font-bold text-jarvisCyan mb-4">Screen Vision Assistant</h1>
      <div className="bg-jarvisPanel border border-jarvisCyan/30 rounded-xl p-4 space-y-4">
        <button
          type="button"
          onClick={createSampleCapture}
          className="px-4 py-2 rounded-lg bg-jarvisCyan text-jarvisBg font-semibold"
        >
          Create Sample Capture
        </button>
        <p className="text-sm text-jarvisGreen">{statusText}</p>
        <ul className="text-sm space-y-1">
          {elements.map((el) => (
            <li key={el.element_id}>
              {el.label} ({el.role}) — ({el.x}, {el.y}, {el.width}x{el.height})
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
