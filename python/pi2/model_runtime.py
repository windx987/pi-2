"""Step 4: the model runtime.

The agent loop does not know any provider. It calls `stream_fn`, which looks up the model's provider in
models.json, resolves its API key, and calls the provider (step 5). Uses the same models.json as Pi.
"""

import json
import os
from pathlib import Path

from . import ai


class ModelRuntime:
    def __init__(self, agent_dir):
        path = Path(agent_dir) / "models.json"
        self.models = []
        if path.exists():
            for provider, config in json.loads(path.read_text()).get("providers", {}).items():
                for model in config.get("models", []):
                    self.models.append({
                        "provider": provider,
                        "id": model["id"],
                        "name": model.get("name", model["id"]),
                        "api": config.get("api", "openai-completions"),
                        "base_url": config["baseUrl"],
                        "api_key": config.get("apiKey", ""),
                        "context_window": model.get("contextWindow", 128000),
                        "max_tokens": model.get("maxTokens"),
                    })

    def find(self, reference=None):
        """Find a model by "provider/id" or "id". Without a reference, the first model in models.json."""
        if not self.models:
            raise SystemExit("No models configured. Add one to models.json (see Getting started in README.md).")
        if reference is None:
            return self.models[0]
        model = self.match(reference)
        if model is None:
            raise SystemExit(f"Model {reference} not found in models.json.")
        return model

    def match(self, reference):
        """The model named "provider/id", "id" or its 1-based number in models.json, or None."""
        if reference.isdigit() and 0 < int(reference) <= len(self.models):
            return self.models[int(reference) - 1]
        for model in self.models:
            if reference in (model["id"], f"{model['provider']}/{model['id']}"):
                return model
        return None

    def stream_fn(self, model, context):
        """Send one request to the model's provider. Yields the provider's events."""
        if model["api"] != "openai-completions":
            raise RuntimeError(f"pi2 supports only the openai-completions API, not {model['api']}.")
        # As in Pi, apiKey may name an environment variable; otherwise it is the key itself.
        api_key = os.environ.get(model["api_key"], model["api_key"])
        return ai.stream(model, context, api_key)
