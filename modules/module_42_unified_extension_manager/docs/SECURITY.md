# Security Architecture — JARVIS Module 42

- **Zero Code Execution During Scanning**: `ModuleArchiveScanner` reads ZIP central directory entries and text files strictly in-memory (`zipfile.ZipFile.open`). It never extracts untrusted archives to disk, never imports packaged Python modules, and never runs setup/install scripts.
- **Archive Safeguards**:
  - Rejects path traversal (`..`), absolute paths (`/`), Windows drive prefixes (`C:`), and null bytes.
  - Rejects POSIX symlinks (`stat.S_ISLNK(info.external_attr >> 16)`).
  - Enforces configurable uncompressed size caps (`JARVIS_M42_MAX_UNCOMPRESSED_MB`), file-count caps (`JARVIS_M42_MAX_ARCHIVE_FILES`), and compression ratio limits (`JARVIS_M42_MAX_COMPRESSION_RATIO`) to stop zip bombs.
  - Runs `zf.testzip()` CRC verification on every archive.
- **Explicit Approval Gate**: Installation plans are always `dry_run: true`, `auto_execute: false`, and require explicit operator approval before any mutating operation.
- **Optional API Token**: Set `JARVIS_M42_API_TOKEN` to require `X-JARVIS-Token` on all mutating endpoints.
