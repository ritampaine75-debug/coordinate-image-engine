# Security and privacy

Coordinate Image Engine treats every JSON document as untrusted input. The renderer intentionally supports a small, declarative graphics language rather than a general-purpose web platform.

## Privacy statement

- The playground has **no telemetry** and no analytics.
- JSON files are read with browser file APIs; their bytes are never uploaded by this application.
- JSON, generated images, error text, and document titles stay in the browser tab.
- The app makes **no `fetch`, `XMLHttpRequest`, WebSocket, EventSource, or external API calls**.
- No external fonts, images, scripts, styles, schemas, or model endpoints are loaded.
- The only persistent browser state is a theme preference in `localStorage`. If storage is blocked, the app still works.
- Clipboard and download actions happen only after an explicit user button press. Blob URLs created for downloads are revoked.
- If a user pastes the master prompt or an image request into a cloud-based chat model, that external provider sees that text. This is separate from the local renderer, which never contacts the provider.

A meta Content Security Policy in `index.html` sets `connect-src 'none'`, `object-src 'none'`, and `base-uri 'none'`, and permits only inline scripts/styles from the single file. Inline execution is required because the core app must work from a standalone `index.html`; it never loads executable code from a URL.

## Untrusted-input defenses

| Defense | Implementation |
|---|---|
| Safe parsing | Only `JSON.parse` is used. The app never uses `eval`, `new Function`, dynamic `import`, or model-provided JavaScript. |
| Strict structure | A Draft 2020-12 schema rejects unknown properties, unsupported types, bad enum values, and out-of-range values. |
| Finite data | Numbers are checked for `NaN`, `Infinity`, and `-Infinity`, including values produced by numeric overflow such as `1e999`. |
| Safe DOM updates | Validation messages and example metadata are inserted with `textContent`, `createElement`, and `replaceChildren`; the app does not use `innerHTML`. |
| Safe text rendering | Model text is drawn with `fillText` / `strokeText`, not inserted into the DOM as HTML. |
| No arbitrary SVG | Path data is parsed into a restricted command list and replayed through Canvas methods. No SVG element or markup string is created. |
| No external resources | Paints are hex colors or named local gradients. `fontFamily` is limited to generic families. URLs are not valid paints. |
| Bounded work | Input size, canvas area, elements, gradients, stops, points, path commands, text length, group depth, stroke settings, shadow settings, and complexity are limited. |
| Error isolation | Each element is rendered inside a saved Canvas state. Validation happens before drawing, and render errors are reported without crashing the whole app. |
| Deterministic control flow | No randomness, timers in the rendering path, remote state, or device-pixel-ratio geometry. |

## Content Security Policy details

The app's CSP allows inline `<script>` and `<style>` because the deployable artifact is one file. It does **not** allow remote script sources, remote styles, plugins, frames, connections, or `unsafe-eval`. The canonical schema and examples are embedded as inert `application/json` or `text/plain` script data, then parsed with `JSON.parse`; they are not executed as JavaScript.

Contributors adding a build step, external asset, or network request would need to revise this policy and the project's local-first guarantee. That should be treated as an architectural change, not a cosmetic one.

## File and clipboard handling

- File input uses the local `File.text()` or `FileReader` API. The file name is shown with `textContent` and never interpreted as HTML.
- Imported text is parsed before being displayed as canonical JSON.
- The optional paste button reads the clipboard only after a user click and reports a clear error if the browser blocks that permission.
- Copy operations use `navigator.clipboard.writeText` when available, with a temporary textarea fallback. The app reports failure rather than pretending success.
- Download filenames are derived from `metadata.title` with Unicode normalization and a safe ASCII slug. They cannot inject paths, HTML, or event handlers.

## Resource-exhaustion model

Even if individual fields are valid, a document could combine many shapes into a slow frame. The runtime validator therefore enforces a combined complexity budget and additional caps on canvas area, recursive elements, path commands, text lines, and export size. A 2× export is rejected when it would exceed 8192 pixels on a side or 16,000,000 pixels total.

Canvas memory can still be affected by browser implementation, hardware acceleration, available RAM, and other tabs. The limits reduce risk; they do not make a browser immune to all denial-of-service conditions.

## Residual risks

- Browser rendering engines can have bugs in Canvas, font, or color parsing. Keep your browser updated.
- Generic fonts and antialiasing can differ between systems, so exported PNGs are deterministic within an environment but may not be byte-identical everywhere.
- Browser extensions with page access can read DOM content, including pasted JSON. Use a clean browser profile for sensitive material.
- A cloud model provider may retain prompts according to its own policy. Use local inference when the image request itself is sensitive.
- Opening a malicious local HTML file purporting to be this project could bypass these guarantees. Obtain `index.html` from a trusted repository and review changes.
- The app does not sandbox third-party iframes; do not embed it in an untrusted host if isolation is required.

## Reporting a vulnerability

Please use the repository's issue tracker for non-sensitive bugs. For a suspected security issue, avoid posting exploit JSON publicly if it could affect users; use GitHub's private security reporting feature if enabled, or contact the maintainers through the repository's listed channel. Include:

1. the affected file and commit;
2. a minimal `coordinate-image-v1` document;
3. browser name and version;
4. observed behavior and expected behavior;
5. whether external network access or script execution occurred.

## Contributor checklist

Before changing the renderer or validator:

- [ ] no new use of `innerHTML`, `eval`, `Function`, dynamic imports, or remote resources;
- [ ] all model-controlled strings are inserted as text, not markup;
- [ ] every new property has schema bounds and a renderer default;
- [ ] new path or text syntax has a strict parser or whitelist;
- [ ] resource limits include the new capability;
- [ ] negative tests cover malformed, excessive, and unsupported values;
- [ ] documentation and the master prompt remain aligned;
- [ ] `connect-src 'none'` and the no-telemetry guarantee still hold.
