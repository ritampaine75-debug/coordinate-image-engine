# Changelog

All notable changes to this project are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project follows semantic versioning for its tooling. The `coordinate-image-v1` drawing contract is stable within major version 1.

## [1.0.0] — 2026-10-26

### Added

- Initial `coordinate-image-v1` protocol with a strict Draft 2020-12 JSON Schema.
- Self-contained `index.html` testing playground with embedded HTML, CSS, JavaScript, schema, examples, and master prompt.
- Deterministic Canvas renderer for rectangles, rounded rectangles, circles, ellipses, lines, polylines, polygons, restricted SVG-style paths, text, groups, transforms, gradients, strokes, dashes, shadows, and opacity.
- Runtime validator with schema checks, finite-number checks, gradient reference checks, unique ids, group-depth limits, path grammar validation, text-line limits, and a combined complexity budget.
- Local JSON upload, drag-and-drop import, clipboard paste where permitted, editable paste area, validation diagnostics, pretty-print, copy JSON, download JSON, clear editor, and reset to a valid example.
- Responsive Canvas preview and PNG export at 1× or 2× document resolution.
- Seven embedded example artworks: sunset landscape, futuristic robot, abstract art, app icon, poster cover, simple diagram, and stylized architecture.
- Reusable `SKILL.md` for compatible agent environments and universal `MASTER_PROMPT.md` for ordinary chat models.
- Optional `/json-image` guidance that clearly distinguishes compatible agent features from ordinary chat behavior.
- Comprehensive README, architecture, protocol, supported-model, troubleshooting, and security documentation.
- MIT license, contribution guide, GitHub issue templates, and a free GitHub Actions validation workflow.
- Python `jsonschema` test suite covering valid examples and malformed, unsupported, invalid-color, out-of-range, and excessive-input cases.
- Dependency-free Node test evaluating the actual inline validator and renderer against all examples and negative cases.
- Optional standard-library maintainer tool that keeps inline assets synchronized with source files.

### Security

- No network requests, telemetry, external assets, remote schemas, API keys, or hidden uploads in the core renderer.
- No `eval`, dynamic function construction, arbitrary HTML insertion, event handlers, or arbitrary SVG markup.
- A restrictive Content Security Policy with `connect-src 'none'`, `object-src 'none'`, and `base-uri 'none'`.
- Bounded input size, canvas area, element count, path complexity, text length, nesting, and export dimensions.

### Known limitations

- Generic fonts and Canvas antialiasing can differ across browsers and operating systems.
- The protocol cannot promise photorealism or replace a native diffusion model for every task.
- Clipboard read/write can be restricted on `file://` or in sandboxed iframes; the app reports those failures clearly.
- 2× export is rejected for documents that would exceed the renderer's memory limits.
