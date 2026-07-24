---
title: Report Generator API
emoji: 📄
colorFrom: indigo
colorTo: teal
sdk: docker
app_port: 7860
pinned: false
---

# Report Generator API

POST /generate with a Python script → returns a .docx report.

## Usage

```bash
curl -X POST http://localhost:7860/generate \
  -H "Content-Type: application/json" \
  -d '{"python_code": "your python code here"}' \
  --output report.docx
