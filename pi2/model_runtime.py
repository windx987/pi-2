"""Step 4: the model runtime.

The agent loop does not know any provider. It calls `stream_fn`, which sends the session's one model
to step 5. Configuration comes from settings.json: providers, each with its models. The runtime flattens
them into one list, the session uses one at a time, and /model switches between them.
"""

import os

from . import ai


def providers(settings):
    """The "providers" mapping, or the old flat "provider" wrapped as one provider."""
    configured = settings.get("providers")
    if isinstance(configured, dict) and configured:
        return configured
    provider = settings.get("provider")
    if isinstance(provider, dict) and provider.get("model"):
        return {
            "custom": {
                **provider,
                "models": [
                    {
                        "id": provider["model"],
                        "name": provider.get("name", provider["model"]),
                        "contextWindow": provider.get("contextWindow", 32768),
                        "maxTokens": provider.get("maxTokens"),
                    }
                ],
            }
        }
    raise SystemExit('Settings: add a "providers" object (or the old "provider").')


class ModelRuntime:
    def __init__(self, settings):
        self.models = []
        for name, config in providers(settings).items():
            api = config.get("api", "openai-completions")
            if api != "openai-completions":
                raise SystemExit(f"Unsupported provider.api for {name}: {api}. Use openai-completions.")
            if not config.get("baseUrl"):
                raise SystemExit(f"Provider {name}: baseUrl is required.")
            base_url = config["baseUrl"].rstrip("/")
            for model in config.get("models") or []:
                self.models.append({
                    "provider": name,
                    "id": model["id"],
                    "name": model.get("name", model["id"]),
                    "api": api,
                    "base_url": base_url,
                    "api_key": config.get("apiKey", ""),
                    "context_window": model.get("contextWindow", config.get("contextWindow", 32768)),
                    "max_tokens": model.get("maxTokens", config.get("maxTokens")),
                })
        if not self.models:
            raise SystemExit('No models configured. Add at least one provider with a model in settings.json.')

    def find(self, reference=None):
        """Find a model by "provider/id" or "id". Without a reference, the first model in settings.json."""
        if reference is None:
            return self.models[0]
        model = self.match(reference)
        if model is None:
            raise SystemExit(f"Model {reference} not found in settings.json.")
        return model

    def match(self, reference):
        """The model named "provider/id", "id" or its 1-based number in settings.json, or None."""
        if reference.isdigit() and 0 < int(reference) <= len(self.models):
            return self.models[int(reference) - 1]
        for model in self.models:
            if reference in (model["id"], f"{model['provider']}/{model['id']}"):
                return model
        return None

    def stream_fn(self, model, context):
        """Send one request to the model's provider. Yields the provider's events."""
        # As in Pi, apiKey may name an environment variable; otherwise it is the key itself.
        api_key = os.environ.get(model["api_key"], model["api_key"])
        return ai.stream(model, context, api_key)
