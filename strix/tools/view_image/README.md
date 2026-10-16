# view_image

SDK-provided tool that loads an image from the sandbox workspace and
returns it as an image content block for vision-capable models.

- **Implementation:** `agents.sandbox.capabilities.tools.view_image.ViewImageTool`
  (upstream `agents` SDK)
- **Wired in:** `strix/agents/factory.py` — added per-run via the SDK
  `Filesystem` capability.
- **Strix defaults:** reads any image the agent has written into the
  sandbox workspace (e.g. a diagram, plot, or rendered contract graph
  under `/workspace`).
- **Recovery:** vision-not-supported model rejections are auto-recovered
  via `strix.core.sessions.strip_all_images_from_session`, invoked from
  `strix/core/execution.py`.
