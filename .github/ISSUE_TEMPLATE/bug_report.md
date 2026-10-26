---
name: Bug report
about: Report incorrect validation, rendering, export, UI, or documentation behavior
title: "[Bug] "
labels: bug
assignees: ''
---

## Summary

Describe the problem in one or two sentences.

## Environment

- Device / operating system:
- Browser and version:
- Opened from: `file://`, local static server, or GitHub Pages
- Repository commit or release:
- Model/provider used to generate JSON, if relevant:

## Steps to reproduce

1.
2.
3.

## Minimal JSON document

If the issue involves a document, paste the smallest complete `coordinate-image-v1` JSON that reproduces it. Remove unrelated elements and do not include secrets.

```json
{
  "protocol": "coordinate-image-v1"
}
```

## Expected behavior

What should the validator or renderer do?

## Actual behavior

What happened instead? Include the exact status or diagnostics text.

## Screenshots or exported PNG

Attach or describe the output if the issue is visual.

## Console errors

Paste relevant browser console errors only if the UI itself failed. Do not paste sensitive data.

## Checklist

- [ ] I reproduced the issue with a current browser.
- [ ] I tried one of the built-in examples.
- [ ] I checked `docs/troubleshooting.md`.
- [ ] I removed secrets and private content from this report.
