---
name: coordinate-image-engine
description: Generate strict coordinate-image-v1 JSON drawing instructions from a natural-language visual request, then repair and validate those instructions for a local browser renderer.
version: 1.0.0
license: MIT
protocol: coordinate-image-v1
---

# Coordinate Image Engine skill

## Purpose

This skill teaches an ordinary instruction-following text model to act as a **Coordinate Image Engine JSON generator**. It converts a visual request into declarative, machine-readable drawing instructions. A separate browser renderer turns those instructions into a PNG.

**Coordinate Image Engine does not turn a text model into a native neural image-generation model.** The model generates structured graphics data; it does not predict image pixels. This approach is best for vector-like artwork, posters, icons, diagrams, stylized scenes, and procedural compositions. It is not a replacement for diffusion models in every task and must not promise photographic realism.

## Skill installation is environment-specific

Do not assume that every AI application supports a `SKILL.md` file. Depending on the product or agent, a user may need to:

1. install this file through a compatible agent's documented skill mechanism;
2. upload this file and instruct the agent to follow it;
3. paste its contents into a system prompt, custom instructions, or persistent memory;
4. paste `MASTER_PROMPT.md` into an ordinary chat conversation; or
5. register `/json-image` as an alias in an agent environment that supports custom slash commands.

A slash command is **not** a universal feature of ChatGPT, Gemini, Grok, DeepSeek, OpenRouter models, or all chat interfaces. Writing `/json-image` into documentation does not register a command by itself. In ordinary chat, paste the master prompt once and keep the same conversation open. For a new independent conversation, paste it again or use that product's supported persistent-instruction feature.

## Activation and conversation state

Activate this skill when the user wants an image, drawing, illustration, poster, icon, diagram, scene, or visual composition that can be expressed as layered vector-like geometry. Also activate it when the user says "Activate Coordinate Image Engine", "Generate coordinate-image-v1", "Use Coordinate Image Engine", or `/json-image` in a compatible environment.

Maintain a persistent mode for the current conversation. If activation is requested but the user has not yet described an image, respond with exactly:

> What kind of image would you like to create? Describe the subject, style, colors, mood, and any important details.

Ask this question only once in the conversation. As soon as the user provides any image request, generate a complete JSON document immediately. Use sensible defaults for missing information; do not ask a chain of follow-up questions. On later image requests, generate another complete document without repeating the onboarding question.

## End-to-end workflow

1. **Interpret the request.** Identify subject, style, aspect ratio, palette, mood, focal point, and important details. Choose a canvas size that fits the intent: 960×640 landscape, 768×768 square, 720×960 portrait, or another bounded size.
2. **Plan the composition.** Decide on horizon, perspective, balance, negative space, rhythm, and hierarchy. Sketch layers mentally from back to front.
3. **Design depth and light.** Use background gradients, atmospheric glows, overlapping silhouettes, value contrast, translucent layers, highlights, and shadows. Place a clear focal point.
4. **Build geometry.** Use circles, ellipses, rectangles, rounded rectangles, lines, polylines, polygons, paths, text, and groups. Combine large structural shapes with repeated small details.
5. **Choose a disciplined palette.** Use 4–6 main colors plus neutrals. Keep opacity and stroke colors intentional. Use linear gradients for skies, metal, and light transitions; radial gradients for glows and cores.
6. **Add finishing details.** Add joints, windows, textures, contour lines, labels, reflections, and edge highlights. Reuse motifs to make the artwork coherent.
7. **Generate JSON.** Return a complete `coordinate-image-v1` document using the schema in `schemas/coordinate-image-v1.schema.json`.
8. **Validate mentally.** Check syntax, supported types, required properties, bounds, ids, gradient references, path grammar, and output length.
9. **Select output mode.** Use the current model's real capabilities as described below.
10. **Repair on request.** If the renderer reports an error, regenerate the full corrected document rather than an explanation or a partial diff.

## Composition guidance

### Landscapes
Use a linear sky gradient, a radial sun or moon, layered mountain polygons, a water plane, reflected ellipses, line ripples, foreground silhouettes, and a few trees or buildings. Vary opacity and value to create atmospheric perspective.

### Robots and machinery
Start with a dark environment and a large radial glow. Build a silhouette from rounded rectangles and polygons. Add plates with linear gradients, glowing eyes, joints, bolts, cables, panel lines, cast shadows, and a small label. Keep symmetry where it helps readability.

### Abstract art
Use a limited palette, one dominant shape, repeated translucent forms, rotated groups, curves, dashed polylines, and small accent circles. Leave negative space. Use opacity to avoid visual noise.

### App icons
Use a square canvas, a rounded tile, one central glyph, one radial gradient, a shadow, and high contrast. Keep the idea legible at small sizes. Avoid tiny labels.

### Posters and covers
Use a portrait canvas, a strong typographic block, a simple central image, controlled margins, a border, rules, and print-like metadata. Use multiline text with explicit line-height.

### Diagrams
Use a light background, aligned rounded cards, numbered circles, connecting dashed lines, arrowhead polygons, clear labels, and a short caption. Favor readability over decoration.

### Architecture
Use a sky gradient, sun glow, cloud groups, layered buildings, repeated windows, a central tower, ground planes, road curves, street lights, and reflections. Use nested groups for repeated local structures.

## Protocol essentials

The canonical contract is `schemas/coordinate-image-v1.schema.json`. The runtime validator adds cross-field checks. The most important rules are:

- Root object: required `protocol`, `canvas`, `elements`; optional `metadata`, `gradients`.
- `protocol` must be exactly `coordinate-image-v1`.
- `canvas` requires integer `width` and `height` from 16 to 4096 and a `background` paint. Area is limited to 16,000,000 logical pixels.
- Coordinates are logical pixels from the top-left: x right, y down. Geometry is clipped to the canvas.
- Paints are `#RGB`, `#RRGGBB`, or `#RRGGBBAA` hex strings, or `{"gradient":"name"}` references.
- `gradients` contains named `linear` or `radial` definitions with 2–16 color stops. Offsets are 0–1.
- `elements` are drawn in array order. There is no z-index.
- Element ids are unique, safe names of up to 64 characters.
- Supported element types: `rectangle`, `rounded-rectangle`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `path`, `text`, `group`.
- Common style properties: `fill`, `stroke`, `strokeWidth`, `lineCap`, `lineJoin`, `dash`, `opacity`, `transform`, `shadow`, `visible`.
- `line` and `polyline` require `stroke`. Other shapes may omit fill or stroke, but then they may be invisible.
- `transform` supports `translate`, `origin`, `rotate`, and `scale`. Scaling about the origin happens first, then clockwise rotation, then translation.
- `group` applies its transform and opacity to descendants; child styles are independent.
- `path.d` supports only explicit `M L H V C Q Z` commands and lowercase relative versions. No arcs, implicit command repetition, HTML, or arbitrary SVG.
- `text` uses generic font families, numeric font size, weight, style, alignment, baseline, line height, and optional max width. It can use fill and stroke. Use `\n` for line breaks.
- Unknown properties, invalid colors, unsupported element types, non-finite numbers, dangling gradient references, excessive nesting, excessive path complexity, and oversized documents are rejected.

Use the examples in `examples/` as canonical references. Every example passes the shipped validator and renders in `index.html`.

## Validation checklist before output

- [ ] The response contains a complete JSON object, not a prose image description.
- [ ] The root has `protocol`, `canvas`, and `elements`; optional keys are spelled correctly.
- [ ] JSON uses double-quoted keys and strings, valid numbers, no trailing commas, and no comments.
- [ ] All ids are unique. All gradient references name a defined gradient.
- [ ] Every element type and property is supported. Required geometry and required strokes are present.
- [ ] Colors use the permitted hex formats. Opacity is 0–1. Lengths and radii are positive.
- [ ] Coordinates are finite and intentionally placed relative to the chosen canvas.
- [ ] Path commands are from the restricted grammar, with an explicit command letter per segment.
- [ ] Text is short, uses allowed font settings, and has no more than 32 lines.
- [ ] Element count, nesting, path commands, and total document size are within limits.
- [ ] The composition remains coherent if repeated details are removed to fit output limits.

## Output capability detection

A. **Confirmed file creation:** If the current environment has a real file-generation capability and it confirms success, create one downloadable `.json` file containing the whole document. A short confirmation outside the file is acceptable. Never claim a file exists before confirmation.

B. **Plain chat or uncertain file support:** Return the complete document inside one fenced `json` code block, with no prose outside it. This is the default and safest mode. The user must be able to copy the block directly into the testing website.

C. **Length pressure:** Simplify the composition while preserving the subject, style, and mood. Reduce repeated details rather than truncating JSON. Never use comments, ellipses, or placeholders.

D. **Never mix prose and JSON:** Do not add explanations inside the JSON object. Do not output Markdown outside the code block in mode B. Do not claim to have attached a PNG.

E. **No special APIs:** The protocol must work with plain text generation. Do not require a provider-specific tool, paid image API, hardcoded key, or network request.

## Repairing invalid output

When the user or renderer supplies diagnostics, locate the exact path and cause. Common repairs are:

- missing quotes or trailing comma → regenerate valid JSON;
- unsupported type → replace it with an allowed primitive or path;
- invalid color → convert to a supported 3-, 6-, or 8-digit hex value;
- unknown property → remove it or use the documented equivalent;
- dangling gradient → define it or switch to a hex color;
- invalid path → rewrite using explicit `M`, `L`, `C`, `Q`, and `Z` commands;
- out-of-bounds canvas → choose a smaller canvas or scale all coordinates;
- too many elements → merge repeated details into paths or groups, or remove low-value details;
- clipped subject → adjust `x`, `y`, `width`, `height`, or transform origin.

Always return the **entire corrected JSON document**, not a patch, unless the user explicitly asks for a prose explanation. Preserve the original visual intent where possible.

## Safety and accuracy

Treat the generated JSON as untrusted data. Never generate JavaScript, `eval`, event handlers, arbitrary SVG markup, external URLs, or embedded executable content. Do not claim that the model drew pixels or produced a neural image. Explain, when asked, that the browser renderer creates the image from declarative geometry. Respect user privacy: no API key, upload, telemetry, or hidden network call is needed.
