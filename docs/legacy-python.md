# Legacy Python App

The Python/FastAPI implementation is retained as a reference implementation and
baseline generator. It is no longer the primary desktop packaging path.

## Why It Stays in the Repository

- It documents the behavior of the original application.
- It provides baseline SVG, palette and metadata outputs for comparison.
- It keeps the browser/FastAPI fallback available during migration checks.
- It avoids losing useful implementation history before the native app has seen
  broader real-world testing.

## What the Native Release Uses

The Tauri/Rust desktop release does not use:

- `backend/`;
- `desktop_main.py`;
- `venv/`;
- `requirements*.txt`;
- NumPy, scikit-learn, scikit-image or Python Potrace packages.

The native release uses:

- `frontend/`;
- `src-tauri/`;
- `src-tauri/vendor/potrace/`.

## Run the Legacy Web App

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

## Regenerate Baseline Outputs

```bash
venv/bin/python tools/generate_legacy_baseline.py
```

Outputs are written to:

```text
tests/baseline/reference/
```

## Future Cleanup Option

After the native app has been validated on macOS and Windows releases, the
legacy files can be moved under a dedicated `legacy/` directory. That move is
intentionally deferred because it would require updating baseline scripts,
legacy helper scripts and documentation all at once.
