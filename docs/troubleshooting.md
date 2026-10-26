# Troubleshooting

Start by opening the browser's developer console only if the UI itself fails to initialize. Normal JSON errors are shown in the **Validation diagnostics** panel and do not require the console.

## JSON parsing errors

| Message or symptom | Cause | Fix |
|---|---|---|
| `JSON syntax error … Unexpected token` | A comma, quote, or bracket is missing, or prose was pasted with the JSON. | Copy only the JSON object or a single complete fenced `json` block. Check the reported line and column. |
| `Unbalanced Markdown code fence` | The model returned an opening fence but no closing fence. | Add one closing ```` ``` ```` or remove all Markdown fences. |
| `The root value must be a JSON object` | The paste starts with an array, string, or number. | Paste the complete object starting with `{ "protocol": ... }`. |
| `JSON editor is empty` | No input or only whitespace. | Paste JSON, upload a file, or load an example. |
| `JSON input exceeds …` | The document is larger than 512 KiB. | Remove repeated details, use grouped structures more efficiently, or ask the model for a simpler composition. |

`JSON.parse` does not accept comments, trailing commas, single quotes, unquoted keys, `NaN`, `Infinity`, or JavaScript expressions.

## Validation diagnostics

| Diagnostic | Cause | Fix |
|---|---|---|
| `Value must equal "coordinate-image-v1"` | Wrong or missing protocol id. | Set root `protocol` to `coordinate-image-v1`. |
| `Missing required property "canvas"` / `"elements"` | A required root field is absent. | Add the field with the shape shown in the minimal example. |
| `Unknown property "…" ` | A model invented a field or misspelled a supported one. | Remove it or use the documented equivalent. The schema is strict. |
| `Unsupported element type "…" ` | The element type is not in v1. | Use `rectangle`, `rounded-rectangle`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `path`, `text`, or `group`. |
| `String does not match the required format` on a color | A CSS name, `rgb(...)`, or malformed hex value was used. | Use `#RGB`, `#RRGGBB`, or `#RRGGBBAA`. |
| `Must be at most 4096` | Canvas width/height is too large. | Reduce the canvas and scale coordinates. |
| `Canvas area exceeds …` | Width times height exceeds 16,000,000 pixels. | Choose a smaller canvas. |
| `Must contain at most 1000 items` / `element count exceeds` | Too many elements, including nested ones. | Merge repeated shapes into polygons/paths or remove low-value detail. |
| `Gradient reference "…" is not defined` | A paint object refers to a missing top-level gradient. | Define the gradient in `gradients` or replace the paint with a hex color. |
| `Duplicate element id "…" ` | Two elements use the same id. | Give every element a unique id. |
| `Group nesting exceeds 8 levels` | Groups are nested too deeply. | Flatten the structure. |
| `explicit command letter` | A path uses implicit SVG command repetition. | Write `L` before every line target, `C` before every cubic curve, and so on. |
| `Path contains a character outside the restricted grammar` | An arc, smooth curve, HTML, or other command was used. | Use only `M L H V C Q Z` and lowercase relative versions. |
| `Text exceeds 32 lines` | Too many `\n` line breaks. | Split content into multiple text elements or shorten it. |
| `Complexity budget … exceeds` | Many shapes, points, path commands, or text lines combine into an expensive frame. | Reduce repeated details or use fewer points/commands. |
| `non-finite` / `1e999` | A number overflows to Infinity. | Use ordinary finite numeric values. |

Validation errors include a path such as `$.elements[3].stroke`. Count from zero when locating an element.

## Rendering problems

### The image is blank but validation passes
- The elements may have no `fill` and no `stroke`.
- `opacity` may be `0`, or `visible` may be `false`.
- Geometry may be outside the canvas and clipped.
- A very light element may be invisible against a light background.

Load an example to confirm the renderer works, then compare its paints with your document.

### The subject is clipped
Coordinates are not auto-scaled. Reduce shape sizes or transforms, or increase the canvas width and height within the documented limits.

### Gradients look wrong
Gradient coordinates are in element user space. Make sure the linear start/end points or radial center/radius cover the intended area. Remember that transforms affect both geometry and gradient coordinates.

### Text looks different on another device
Only generic font families are allowed. Glyph shapes and metrics can vary by OS and browser. Use shorter strings and avoid pixel-perfect typography when cross-platform identity is required.

### PNG export fails
- 2× export may exceed the 8192-pixel or 16,000,000-pixel export limit. Choose 1×.
- The browser may be out of memory. Close other canvases or reduce document dimensions.
- Very old browsers may not support `canvas.toBlob`. Use a current Android or desktop browser.

### The preview looks sharp/unsharp on a high-DPI display
The preview is a logical-resolution Canvas scaled by CSS. PNG export is generated from the same logical document at 1× or re-rendered at 2×. This is intentional and keeps output deterministic.

## File import, clipboard, and download

### File upload does nothing
- Check that the file has a `.json` extension or `application/json` type.
- Check that it is smaller than 512 KiB.
- On Android, use the system file picker and avoid cloud providers that pass a non-JSON temporary name.
- Drag-and-drop is optional; use **Choose JSON file** if the browser does not expose dropped files.

### Paste JSON button says clipboard access is blocked
`navigator.clipboard.readText()` requires a secure context and user permission in many browsers, and may be unavailable from `file://`. Use the editor and your device's normal paste gesture (`Ctrl+V`, `Cmd+V`, or long-press **Paste**).

### Copy JSON says clipboard access is blocked
The app tries the Clipboard API and then a local selection-based fallback. If both are blocked, select the editor text and use the browser's copy command.

### Download does not start
Some browsers disable programmatic downloads from sandboxed iframes or strict `file://` settings. Open `index.html` directly in a normal browser tab, or serve the repository with `python3 -m http.server 8000` and open the local address. No backend code is involved.

## Model-output problems

| Symptom | Fix |
|---|---|
| The model describes the image in prose instead of returning JSON. | Start a fresh chat, paste the full master prompt first, then repeat the image request. |
| The model repeats the onboarding question. | Keep the original conversation open and remind it that Coordinate Image Engine mode is already active. |
| The model claims a file was created but none exists. | Ask for the complete JSON in one fenced `json` block. Never rely on an unconfirmed attachment. |
| The JSON is truncated. | Ask for a simplified composition with at most 40 elements. |
| The model uses unsupported CSS colors or SVG features. | Paste the validation diagnostics and request a full corrected document. |
| Every revision invents new properties. | Include `skill/SKILL.md` or the canonical schema in the model's context, and ask it to follow only allowed types. |

## GitHub Pages and local files

- The app works from `index.html` with no build step. Relative links to documentation work from the repository or GitHub Pages.
- If a documentation link downloads a Markdown file instead of rendering it, that is normal for static hosting; open it from the repository on GitHub.
- If you edit the schema, master prompt, or examples, run `python3 tools/update-index-assets.py` to refresh the inline copies. CI runs the same tool with `--check`.
- A browser extension that blocks inline scripts can prevent the app from loading. Allow scripts for the local page or use a private window with extensions disabled.
- If the UI stays on “Loading a valid example”, JavaScript is disabled or an error occurred while reading the embedded assets. Check that `index.html` was copied in full and not truncated.

## Useful local checks

```sh
python3 tools/update-index-assets.py --check
node tests/runtime-validator.test.mjs
python3 -m pip install jsonschema
python3 tests/validate_documents.py
```

The Node test needs no packages. The Python test needs the free, open-source `jsonschema` package.
