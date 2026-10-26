# Coordinate Image Protocol v1 — specification

**Protocol identifier:** `coordinate-image-v1`  
**Status:** stable for version 1  
**Canonical schema:** [`../skill/schemas/coordinate-image-v1.schema.json`](../skill/schemas/coordinate-image-v1.schema.json)  
**Reference renderer:** [`../index.html`](../index.html)

## 1. Scope and purpose

`coordinate-image-v1` is a declarative JSON format for two-dimensional vector-like drawings. A text model generates drawing instructions; a separate browser renderer validates those instructions and paints them onto an HTML Canvas. The protocol contains no executable code, external resources, URLs, arbitrary HTML, or arbitrary SVG markup.

The protocol is **not** a pixel tensor, neural image format, or claim that a text model can directly synthesize images. It is a portable intermediate representation between language-model output and a deterministic graphics engine.

## 2. Document structure

Every document is one JSON object. The root allows exactly five properties:

| Property | Required | Type | Meaning |
|---|---:|---|---|
| `protocol` | yes | string | Must equal `coordinate-image-v1`. |
| `canvas` | yes | object | Canvas size and background paint. |
| `elements` | yes | array | Ordered drawing operations, back to front. |
| `metadata` | no | object | Human-readable title, description, author, license, and tags. |
| `gradients` | no | object | Named linear and radial gradient definitions. |

Unknown root properties are rejected. The same strict rule applies to nested objects.

A minimal valid document is:

```json
{
  "protocol": "coordinate-image-v1",
  "canvas": {
    "width": 640,
    "height": 360,
    "background": "#101820"
  },
  "elements": [
    {
      "id": "sun",
      "type": "circle",
      "x": 320,
      "y": 180,
      "radius": 90,
      "fill": "#FFD166"
    }
  ]
}
```

`metadata` may contain `title` (1–120 characters), `description` (1–500), `author` (1–120), `license` (1–120), and `tags` (at most 16 strings of at most 40 characters). Metadata does not affect rendering.

## 3. Coordinate system and canvas

- `width` and `height` are integers from **16 through 4096**.
- The product `width × height` must be at most **16,000,000** logical pixels.
- Coordinates are logical pixels, with `(0, 0)` at the top-left corner. `x` increases to the right; `y` increases downward.
- There are no normalized coordinates and no implicit responsive scaling. CSS may display the preview at any size, but the document dimensions and exported PNG remain unchanged at 1×.
- Geometry outside the canvas is allowed but clipped by the Canvas viewport.
- `background` is a required paint. It fills the whole canvas before any element is drawn.
- The canvas has no transparency setting; an 8-digit hex background is blended with the initially transparent canvas.

## 4. Colors and paint values

A color is one of these hexadecimal strings:

- `#RGB`
- `#RRGGBB`
- `#RRGGBBAA`

Uppercase and lowercase hexadecimal digits are accepted. `#RRGGBBAA` supplies an alpha channel. CSS color names, `rgb(...)`, `hsl(...)`, URLs, and arbitrary strings are intentionally rejected.

A **paint** is either a color string or a gradient reference:

```json
{"gradient": "sky"}
```

The named gradient must exist as a key in the top-level `gradients` object. Gradient names and element ids match `^[A-Za-z][A-Za-z0-9_-]*$` and contain at most 64 characters.

## 5. Gradients

`gradients` contains at most 64 named definitions. Each definition is either linear or radial and contains 2–16 stops. A stop has an `offset` from 0 through 1 and a valid `color`. Stops need not be sorted; Canvas maps each stop by its offset. Repeated offsets are allowed and produce a hard transition.

### Linear gradient

| Property | Meaning |
|---|---|
| `type` | Must be `linear`. |
| `x1`, `y1` | Start point. |
| `x2`, `y2` | End point. |
| `stops` | Array of 2–16 `{offset, color}` objects. |

The browser uses `CanvasRenderingContext2D.createLinearGradient(x1, y1, x2, y2)`.

### Radial gradient

| Property | Meaning |
|---|---|
| `type` | Must be `radial`. |
| `cx`, `cy` | Center of both circles. |
| `r` | Positive radius of the outer circle. |
| `stops` | Array of 2–16 `{offset, color}` objects. |

The browser uses `createRadialGradient(cx, cy, 0, cx, cy, r)`. There is no separate focal point in v1.

Gradient coordinates are expressed in the current element's user coordinate space. Element and group transforms therefore affect geometry and gradient coordinates together. A gradient reference may be used for `canvas.background`, `fill`, or `stroke`.

## 6. Elements and layer order

`elements` is an array of 0–1000 top-level elements. Elements are painted in **array order**: earlier elements are behind later elements. There is no `z` property and no sorting.

Every element requires a unique `id` and a `type`. Ids are case-sensitive and must be unique across the whole document, including inside groups. The supported types are:

`rectangle`, `rounded-rectangle`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `path`, `text`, `group`.

### Common optional style properties

Unless noted otherwise, an element may use:

| Property | Type / range | Default | Behavior |
|---|---|---|---|
| `fill` | paint | none | Fill is skipped if omitted. |
| `stroke` | paint | none | Outline is skipped if omitted. |
| `strokeWidth` | number `> 0`, `<= 128` | `1` | Width in logical user units. |
| `lineCap` | `butt`, `round`, `square` | `butt` | Applies to open strokes. |
| `lineJoin` | `miter`, `round`, `bevel` | `miter` | Applies to stroked joins. |
| `dash` | 1–16 positive numbers, each `<= 1024` | `[]` | Repeating dash pattern for strokes. |
| `opacity` | number `0..1` | `1` | Multiplies group-inherited alpha. |
| `transform` | object | identity | See section 7. |
| `shadow` | object | none | See below. |
| `visible` | boolean | `true` | `false` skips the element and, for groups, its descendants. |

`shadow` requires `color` and `blur` (0–128), and accepts `offsetX` and `offsetY` from -256 through 256, defaulting to 0. It is implemented with Canvas shadow properties and is affected by the effective element opacity.

Fill and stroke are separate paint values. For normal shapes, the renderer calls `fill()` first and `stroke()` second, so the stroke is on top. If both are omitted, the element is valid but invisible.

### 6.1 `rectangle`

Required geometry: `x`, `y`, `width`, `height`. Width and height must be positive. The rectangle is axis-aligned. There is no corner radius on this type; use `rounded-rectangle`.

### 6.2 `rounded-rectangle`

Required geometry: `x`, `y`, `width`, `height`, `radius`. Radius is 0–4096. The renderer clamps it to half of the smaller side, so an oversized radius produces a pill or circle-like shape rather than an error. A radius of `0` is equivalent to a plain rectangle.

### 6.3 `circle`

Required geometry: center `x`, `y`, and positive `radius`. A full circle is drawn.

### 6.4 `ellipse`

Required geometry: center `x`, `y`, positive `radiusX`, and positive `radiusY`. The ellipse is axis-aligned unless the whole element is transformed.

### 6.5 `line`

Required geometry: `x1`, `y1`, `x2`, `y2`. A `stroke` paint is required; without a visible stroke a line has no pixels. `fill` is not accepted.

### 6.6 `polyline`

Required geometry: `points`, an array of 2–256 `[x, y]` pairs. A `stroke` paint is required. The path is open and is not automatically closed. `fill` is not accepted.

### 6.7 `polygon`

Required geometry: `points`, an array of 3–256 `[x, y]` pairs. The renderer connects all points and closes the subpath. Both fill and stroke are optional. Self-intersecting polygons use the Canvas nonzero fill behavior.

### 6.8 `path`

Required geometry: `d`, a string of 2–8192 characters using the restricted grammar in section 8. Fill and stroke are optional. Path data is parsed into internal drawing commands; it is never inserted into the DOM as SVG markup.

### 6.9 `text`

Required geometry: `x`, `y`, and `text` (1–512 characters). Text is drawn with the Canvas text API and does not create DOM nodes.

| Property | Allowed values | Default |
|---|---|---|
| `fontSize` | number `> 0`, `<= 256` | `32` |
| `fontFamily` | `sans-serif`, `serif`, `monospace`, `system-ui` | `sans-serif` |
| `fontWeight` | `normal`, `bold`, or `"100"`–`"900"` | `normal` |
| `fontStyle` | `normal`, `italic` | `normal` |
| `align` | `left`, `center`, `right` | `left` |
| `baseline` | `alphabetic`, `top`, `middle`, `bottom` | `alphabetic` |
| `lineHeight` | number `0.5..3` | `1.2` |
| `maxWidth` | number `> 0`, `<= 4096` | none |

A `\n` escape starts a new line. At most 32 lines are allowed. The `y` coordinate anchors the **first** line according to `baseline`; each additional line is drawn at `y + index × lineHeight × fontSize`. `maxWidth` is passed to Canvas's optional text width argument. For text, `strokeText()` is called before `fillText()` so a filled glyph remains readable when both paints are set.

Only generic font families are accepted. This avoids external font downloads, but exact glyph rasterization can vary by browser and operating system.

### 6.10 `group`

Required geometry: `children`, a nonempty array of elements. A group may use `opacity`, `transform`, and `visible`. It has no own fill, stroke, or shadow.

Group opacity multiplies the opacity of every descendant. Group transform applies to all descendants. A child may also have its own transform and opacity; child transforms compose with parent transforms in normal Canvas matrix order. Child styles are **not inherited**: every shape or text element must declare its own paints and typography.

Groups can nest up to 8 levels, counting the top-level element list as level 1. The recursive element total, including groups, is at most 1000.

## 7. Transforms

An optional `transform` object may contain:

| Property | Type / range | Default |
|---|---|---|
| `translate` | `[x, y]`, each `-100000..100000` | `[0, 0]` |
| `origin` | `[x, y]`, each `-100000..100000` | `[0, 0]` |
| `rotate` | degrees `-3600..3600` | `0` |
| `scale` | `[x, y]`, each `> 0`, `<= 100` | `[1, 1]` |

At least one property must be present. Coordinates are transformed by this ordered formula:

1. subtract `origin` from the point;
2. multiply x by `scale[0]` and y by `scale[1]`;
3. rotate by `rotate` degrees, clockwise in the screen coordinate system;
4. add `origin` back;
5. add `translate`.

The renderer implements this with `translate`, `origin`, `rotate`, `scale`, and inverse-origin Canvas operations in that order. A group transform is applied before its children's local transforms. Transforms do not change the logical canvas dimensions.

## 8. Restricted path grammar

`path.d` is a constrained subset of SVG path data. It is parsed by the application, not handed to the browser as markup.

Allowed absolute commands:

| Command | Arguments | Meaning |
|---|---:|---|
| `M` | `x y` | Start a new subpath. |
| `L` | `x y` | Line to a point. |
| `H` | `x` | Horizontal line to x. |
| `V` | `y` | Vertical line to y. |
| `C` | `x1 y1 x2 y2 x y` | Cubic Bézier curve. |
| `Q` | `x1 y1 x y` | Quadratic Bézier curve. |
| `Z` | none | Close the current subpath. |

Lowercase `m l h v c q z` are the relative versions. Relative coordinate pairs in `c` and `q` are all relative to the point at the start of that segment, not to preceding control points.

Rules:

- The first command must be `M` or `m`.
- Every segment must start with its own explicit command letter. Implicit repetition such as `L 1 2 3 4` is rejected.
- Numbers may be integers, decimals, signed, or in scientific notation. Every number must be finite and have absolute value at most 1,000,000.
- Whitespace and commas separate tokens. No other characters are allowed.
- `Z` closes to the most recent `M` start point and takes no arguments.
- Arcs (`A`), smooth curves (`S`, `T`), catmull-rom commands (`R`), multiple subpath parameters after one command, embedded markup, and external references are rejected.
- Each path has at most 256 commands. All paths in a document have at most 4096 commands combined.

Example:

```text
M 40 420 C 160 360 260 450 380 390 C 500 330 620 410 920 350 L 920 640 L 40 640 Z
```

## 9. Validation model

The repository ships two complementary validators:

1. **Canonical JSON Schema** — Draft 2020-12, at `skill/schemas/coordinate-image-v1.schema.json`. CI validates it with Python `jsonschema`. It uses local `$defs`/`$ref` only; there are no remote references.
2. **Browser runtime validator** — embedded in `index.html`. It evaluates the same embedded schema with a small safe subset of JSON Schema keywords used by this project, then performs the cross-field checks below. It never calls `eval`, loads remote schemas, or executes model-provided code.

Runtime-only checks include:

- finite numbers anywhere in the parsed document;
- canvas area;
- unique element ids;
- existing gradient references;
- recursive element count and group depth;
- restricted path grammar and total path-command budget;
- maximum text lines;
- overall complexity budget.

A document must pass both schema and runtime checks before rendering. Errors include a JSON path and an actionable message.

### Complexity budget

The budget is **50,000 units** per document:

- 2 units per gradient definition, plus 2 per gradient stop;
- 1 per element, including groups;
- 2 per point pair;
- 8 per path command;
- 6 per text line;
- 1 per dash-array value;
- 2 per transform.

The budget prevents many individually valid elements from combining into an expensive frame.

## 10. Resource limits

| Resource | Limit |
|---|---|
| Editor text | 524,288 characters |
| Imported file | 524,288 bytes |
| Canvas width / height | 16–4096 logical pixels each |
| Canvas area | 16,000,000 logical pixels |
| Top-level / recursive elements | 1000 |
| Group nesting | 8 levels |
| Gradients / stops | 64 / 2–16 each |
| Coordinate magnitudes | 100,000 |
| Polyline / polygon points | 2–256 / 3–256 |
| Path characters / commands | 8192 / 256 per path |
| Total path commands | 4096 |
| Text characters / lines | 512 / 32 |
| Font size / stroke width | 256 / 128 |
| Render/export scale | `> 0`, at most `2` |
| Export dimensions | 8192 per side and 16,000,000 pixels total |

At 2× export, large documents can exceed the export memory limit. Use 1× or reduce canvas dimensions in that case.

## 11. Rendering behavior

A renderer must:

1. parse JSON strictly with `JSON.parse` (no comments or trailing commas);
2. verify the protocol identifier;
3. validate the schema and runtime limits;
4. set the Canvas bitmap to the document's logical dimensions at 1×;
5. fill the entire background;
6. iterate `elements` in array order;
7. apply visibility, group transform, group opacity, element transform, and element opacity;
8. construct each geometry path from declarative data only;
9. apply paints, gradients, stroke settings, shadows, and typography;
10. fill before stroke for shapes, and stroke before fill for text;
11. clip drawing to the canvas;
12. report errors without executing untrusted code;
13. preserve the source JSON separately from the raster output.

The supplied renderer uses no random numbers, current time, network data, external fonts, stored state, or device-pixel-ratio-dependent geometry. For a fixed document and rendering configuration, drawing order and geometry are deterministic within a given browser and graphics environment. Antialiasing, 8-digit hex interpretation, shadow rasterization, and generic-font glyphs may vary slightly across browser engines; cross-browser pixel-identical output is therefore not promised.

## 12. Error conditions

A renderer must reject:

- malformed JSON or a non-object root;
- a missing or incorrect protocol identifier;
- missing required fields and unknown properties;
- unsupported element types or path commands;
- invalid color formats;
- non-finite numbers, NaN, or Infinity;
- out-of-range dimensions, lengths, opacity, text, or path complexity;
- dangling gradient references;
- duplicate ids;
- excessive nesting, elements, or complexity units;
- any attempt to include executable code, URLs, HTML, event handlers, or arbitrary SVG.

`JSON.parse` treats duplicate object keys with normal last-value-wins behavior. Authors should not generate duplicate keys; the protocol's uniqueness rule applies to element `id` values, not JSON object keys.

## 13. Versioning and extensions

The `protocol` string is the compatibility boundary. A renderer claiming `coordinate-image-v1` support must implement all types and semantics in this document, reject unsupported properties, and avoid silently ignoring errors. Additions that change rendering should use a new protocol identifier rather than altering v1 examples in place.
