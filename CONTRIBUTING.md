# Contributing to Coordinate Image Engine

Thank you for helping keep this project useful, safe, and accessible. Contributions are welcome from desktop editors, GitHub's web interface, and mobile environments such as Termux.

## Project principles

1. **No mandatory build step.** `index.html` must remain directly usable and deployable on GitHub Pages.
2. **No paid services or secrets.** The core app must work with no API key, backend, telemetry, or external asset.
3. **Strict by default.** Untrusted JSON is validated before drawing. Unknown properties and unsafe features are rejected.
4. **Local-first.** Files, JSON, and images stay in the browser unless the user explicitly copies them elsewhere.
5. **Accurate claims.** This is procedural graphics generation, not native neural image generation.
6. **Accessible and mobile-friendly.** Use semantic HTML, visible focus states, sufficient contrast, and native controls.

## Ways to contribute

- Fix documentation, typos, or confusing diagnostics.
- Add a valid example document for a new visual category.
- Improve model instructions without making them provider-specific.
- Add negative tests for invalid JSON or resource abuse.
- Improve Canvas rendering while preserving deterministic behavior and the protocol contract.
- Improve accessibility or responsive layout in `index.html`.
- Report compatibility results for free-access or local text models.

Please use the provided [bug report](.github/ISSUE_TEMPLATE/bug_report.md) and [feature request](.github/ISSUE_TEMPLATE/feature_request.md) templates when applicable.

## Editing from GitHub web or Termux

The core files are plain HTML, Markdown, and JSON. You can edit them directly on GitHub's website. For a local clone:

```sh
git clone <your-fork-url>
cd coordinate-image-engine
git checkout -b my-change
# edit files
python3 tools/update-index-assets.py --check
node tests/runtime-validator.test.mjs
python3 -m pip install jsonschema
python3 tests/validate_documents.py
git add .
git commit -m "Describe your change"
git push -u origin my-change
```

Termux packages, if needed:

```sh
pkg install git python nodejs
python3 -m pip install jsonschema
```

The optional `jsonschema` package is for CI-style validation only; the app and Node runtime test need no installed dependencies.

## Keeping `index.html` synchronized

`index.html` embeds three source assets so it can work from `file://` with no fetch calls:

- `skill/schemas/coordinate-image-v1.schema.json`;
- all files in `skill/examples/`;
- `skill/MASTER_PROMPT.md`.

After editing any of them, run:

```sh
python3 tools/update-index-assets.py
```

The generated blocks are clearly marked. Do not hand-edit those blocks. CI verifies them with `--check`.

## Protocol changes

A change to the protocol is a coordinated change. Update all of the following in one pull request:

1. `skill/schemas/coordinate-image-v1.schema.json`;
2. the validator, renderer, and limits in `index.html`;
3. `docs/protocol-specification.md`;
4. `skill/MASTER_PROMPT.md` and `skill/SKILL.md`;
5. `tests/validate_documents.py` and `tests/runtime-validator.test.mjs`;
6. at least one valid example and relevant negative tests;
7. README compatibility and limitation notes;
8. `CHANGELOG.md`.

Do not silently change how an existing valid v1 document renders. If rendering semantics must change, discuss a new protocol identifier.

Never add external images, fonts, scripts, styles, arbitrary SVG injection, `eval`, `new Function`, remote schemas, or model-provider API calls.

## Example-document checklist

- [ ] `protocol` is exactly `coordinate-image-v1`.
- [ ] `metadata.title` and `description` are meaningful.
- [ ] All ids are unique.
- [ ] All gradient references are defined.
- [ ] Colors use supported hex formats.
- [ ] Geometry fits the intended composition and uses layering intentionally.
- [ ] The document passes both test suites.
- [ ] The thumbnail renders correctly in the gallery.
- [ ] The file is reasonably sized for mobile browsers.

## UI and JavaScript style

- Keep all app code inside `index.html`; do not introduce a mandatory module bundler.
- Use plain JavaScript without external libraries.
- Insert untrusted strings with `textContent` or `createElement`, never `innerHTML`.
- Keep DOM lookups and event wiring inside `initApp()` so pure validator/renderer functions remain testable in Node.
- Prefer clear names and small pure functions over clever abstractions.
- Preserve keyboard navigation and visible focus indicators.
- Do not add decorative animations or emoji to the application UI.

## Pull request checklist

- [ ] The change works when `index.html` is opened directly.
- [ ] The change works on a narrow mobile viewport.
- [ ] No external network request or secret was added.
- [ ] `python3 tools/update-index-assets.py --check` passes.
- [ ] `python3 tests/validate_documents.py` passes.
- [ ] `node tests/runtime-validator.test.mjs` passes.
- [ ] Documentation and changelog are updated.
- [ ] The PR explains any protocol or rendering behavior change.

## Security issues

For a suspected vulnerability, follow [`docs/security.md`](docs/security.md). Avoid posting a working exploit publicly. Include a minimal document, browser version, and expected behavior.

## License

By contributing, you agree that your contribution is licensed under the repository's [MIT License](LICENSE).
