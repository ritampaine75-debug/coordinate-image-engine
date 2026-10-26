# Supported models and compatibility

The protocol is provider-independent. Any instruction-following text model that can produce a complete JSON object can participate. The browser renderer never contacts a model provider and never needs an API key.

This repository does **not** certify a provider's current free tier, rate limit, JSON reliability, or product features. Those change frequently. Verify them in the provider's own documentation.

## Three different meanings of “free”

| Access type | What it means | Privacy / dependency notes |
|---|---|---|
| Free model access in a web app | A chat product lets some users send prompts at no monetary cost. | The provider still receives the prompt. The core renderer remains independent. |
| Free API quota | An API provider grants a no-cost monthly, daily, or trial quota. | May require an account and key. Not needed by this project. |
| Completely local inference | A model runs on the user's hardware through a local tool such as Ollama, llama.cpp, LM Studio, or a similar runtime. | Prompts and output stay local, subject to that tool's behavior. Requires enough RAM and a suitable model file. |

The testing playground itself is always free, local, and usable without any model. You can hand-write JSON, load examples, and export images from static files.

## Product families

| Product family | Typical integration | Capability considerations |
|---|---|---|
| ChatGPT / OpenAI chat | Paste `MASTER_PROMPT.md` into a new chat. | File creation depends on the current product and plan. If unsure, the model must return one fenced `json` block. Do not assume a file was attached. |
| Gemini consumer or AI Studio | Paste the prompt into the product's instruction area or first message. | JSON mode and file creation differ by interface. Keep the conversation open for follow-up revisions. |
| Grok | Paste the prompt in a new conversation. | Treat any free access as an availability detail that can change. Use the code-block output policy by default. |
| DeepSeek chat | Paste the prompt at the start of a chat. | Long contexts and output limits vary. Ask for a simplified composition if a response is cut off. |
| OpenRouter-hosted models | Select an instruction-following model with sufficient output length, then paste the prompt. | Quality depends on the specific hosted model, its context window, sampling settings, and any active quota. OpenRouter is a router, not one fixed model. |
| Local models | Provide `SKILL.md` or `MASTER_PROMPT.md` as the system prompt. | Prefer models with reliable instruction following and valid JSON generation. Small models may need shorter compositions and a repair loop. |
| Other chat models | Use the same universal prompt in any product that supports persistent conversation instructions. | A slash command is not universal; pasting the prompt is the portable path. |

No provider-specific API call, SDK, schema extension, or hidden key is part of the protocol.

## Smoke test for a model

Use this conversation sequence:

1. Paste the contents of `MASTER_PROMPT.md` and submit it as the first instruction.
2. Send: `Activate Coordinate Image Engine.`
3. Expected first reply, exactly: `What kind of image would you like to create? Describe the subject, style, colors, mood, and any important details.`
4. Send: `Create a premium futuristic robot with metallic armor, cyan lighting, realistic mechanical details, and a dark sci-fi background.`
5. Expected next reply: a complete `coordinate-image-v1` JSON document, either in a confirmed downloadable file or one fenced `json` code block.
6. Send: `Now create a sunset landscape.`
7. Expected next reply: another complete JSON document, with no onboarding question repeated.

Copy the JSON into `index.html`, choose **Validate JSON**, then **Render Image**. If the result is invalid, paste the exact diagnostics back to the model and ask it to return the whole corrected document.

## What makes a model work well

- reliable instruction following across multiple turns;
- enough output tokens for 20–120 elements;
- strict JSON generation without trailing commas or comments;
- ability to keep a stable coordinate system and unique ids;
- ability to preserve a palette and composition while revising;
- willingness to output JSON only instead of adding explanations.

A larger model is not automatically better. Deterministic sampling, a clear prompt, and a manageable composition often matter more. If a model supports JSON mode, enable it, but still validate the result: JSON mode does not guarantee protocol conformance.

## Common output adaptations

### The model adds prose around JSON
Tell it: “Return the entire corrected document in one fenced json code block. No prose outside the block.” The app also accepts a single correctly fenced block.

### The model claims to have attached a file
Ignore the claim unless the file is actually available. Ask for the JSON in a fenced code block. The master prompt explicitly forbids unconfirmed file claims.

### The response is truncated
Ask for a simpler version with 20–40 elements and fewer repeated details. A valid simple image is better than an invalid long one.

### Coordinates are inconsistent
Ask the model to fix the canvas dimensions and keep the subject inside them. The renderer will clip out-of-bounds geometry rather than rescale it.

### The model invents unsupported properties
Paste the error path and message. Supported types and properties are listed in the protocol specification and master prompt. Unknown properties are intentionally rejected.

### The model outputs Markdown or HTML
Return to a fresh chat and paste the master prompt again. Do not ask the renderer to parse non-JSON text.

## Optional slash-command workflow

In an agent environment that supports custom commands, register `/json-image` to load `SKILL.md` or `MASTER_PROMPT.md`. This is an environment-specific convenience, not a protocol feature.

- Compatible agent environment: install the skill and register the command alias.
- Environment with uploaded instructions: upload `SKILL.md` and reference it.
- Ordinary chat interface: paste `MASTER_PROMPT.md` once and continue in the same conversation.
- Future independent chats: paste it again or use the product's persistent-instruction mechanism.

## Accuracy statement

The renderer is free and independent of model providers. The model step may use a free web interface, a free API quota, a paid API, or local inference. Availability, quality, privacy, rate limits, and context windows are controlled by those external tools, not by Coordinate Image Engine.
