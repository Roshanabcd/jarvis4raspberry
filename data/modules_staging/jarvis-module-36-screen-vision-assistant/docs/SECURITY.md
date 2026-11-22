# Module 36 — Security & Privacy Notes

- **Local-First Processing**: Image header inspection, SHA-256 hashing, bounding-box hit-testing, and screen Q&A run 100% locally without transmitting screenshots to external APIs.
- **No Unsolicited Desktop Grabbing**: Live OS display capture (X11/Wayland) is intentionally decoupled so captures are only ingested via explicit API submission or user-approved host adapters.
- **Strict Input Validation**: Rejects malformed base64 payloads (`422 INVALID_BASE64_IMAGE`), unsupported binaries (`422 UNSUPPORTED_IMAGE_FORMAT`), duplicate element IDs (`422 DUPLICATE_ELEMENT_ID`), and out-of-bounds bounding boxes/coordinates (`422`).
- **CORS & Storage**: Restrict `JARVIS_M36_CORS_ORIGINS` in production and store `JARVIS_M36_DB_PATH` under an owner-only directory (`chmod 700`).
