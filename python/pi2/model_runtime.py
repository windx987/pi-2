"""Step 4: the model runtime.

The agent loop does not know any provider. It calls `stream_fn`, which sends the one configured
provider's model to step 5. Configuration comes from settings.json.
"""

from . import ai


class ModelRuntime:
    def __init__(self, provider):
        api = provider.get("api", "openai-completions")
        if api != "openai-completions":
            raise SystemExit(f"Unsupported provider.api: {api}. Use openai-completions.")

        self.model = {
            "provider": "custom",
            "id": provider["model"],
            "name": provider.get("name", provider["model"]),
            "api": api,
            "base_url": provider["baseUrl"].rstrip("/"),
            "api_key": provider.get("apiKey", ""),
            "context_window": provider.get("contextWindow", 32768),
            "max_tokens": provider.get("maxTokens"),
        }

    def stream_fn(self, model, context):
        """Send one request to the configured provider. Yields the provider's events."""
        return ai.stream(model, context, model["api_key"])
