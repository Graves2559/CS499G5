# OCR Benchmark — Setup & Run

Terminal commands only. Run everything from inside this project folder.

## 1. Create the virtual environments

**Windows (PowerShell or cmd):**
```
python -m venv .venv
python -m venv .venv-rapidocr
```

**Mac (Terminal):**
```
python3 -m venv .venv
python3 -m venv .venv-rapidocr
```

## 2. Install dependencies

**Windows:**
```
.venv\Scripts\python.exe -m pip install torch transformers pillow psutil huggingface_hub

.venv-rapidocr\Scripts\python.exe -m pip install rapidocr psutil
.venv-rapidocr\Scripts\python.exe -m pip uninstall onnxruntime -y
.venv-rapidocr\Scripts\python.exe -m pip install onnxruntime-directml
```

**Mac:**
```
.venv/bin/python -m pip install torch transformers pillow psutil huggingface_hub

.venv-rapidocr/bin/python -m pip install rapidocr psutil onnxruntime
```
(`onnxruntime-directml` is Windows-only — DirectML doesn't exist on macOS. Plain `onnxruntime` runs on CPU, or CoreML where supported. Add `--no-dml` when running `bench.py` on Mac.)

## 3. Download the TrOCR model weights

**Windows:**
```
.venv\Scripts\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('microsoft/trocr-base-handwritten', local_dir='models/trocr-base-handwritten')"
```

**Mac:**
```
.venv-rapidocr/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('microsoft/trocr-base-handwritten', local_dir='models/trocr-base-handwritten')"
```

## 4. Fix the GNHK dataset (run once)

Repairs a known download issue where some `.jpg`/`.json` file pairs got swapped.

**Windows:**
```
.venv-rapidocr\Scripts\python.exe fix_gnhk_extensions.py dataset\GNHK-dataset-main
```

**Mac:**
```
.venv-rapidocr/bin/python fix_gnhk_extensions.py dataset/GNHK-dataset-main
```

## 5. Clean up / organize the project folder (run once)

**Windows:**
```
.venv\Scripts\python.exe organize_project.py
```

**Mac:**
```
.venv/bin/python organize_project.py
```

## 6. Run the benchmarks

**Windows:**
```
.venv\Scripts\python.exe bench.py --engine trocr --images-dir dataset --limit 100
.venv-rapidocr\Scripts\python.exe bench.py --engine rapidocr --images-dir dataset --limit 100
```

**Mac:**
```
.venv/bin/python bench.py --engine trocr --images-dir dataset --limit 100
.venv-rapidocr/bin/python bench.py --engine rapidocr --images-dir dataset --limit 100 --no-dml
```

Results are written to `results/ocr_benchmark_<engine>.csv`.

## Notes

- GPU utilization/memory logging (the `gpu_percent`/`gpu_memory_mb` columns) uses Windows-only performance counters. On Mac these columns will always read "unavailable" — this is expected, not a bug.
- Reactivating an existing venv in a new terminal never requires reinstalling packages — see the venv explanation earlier in this project's chat log if that's unclear.
