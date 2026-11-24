# Connect a model

pi2 talks to any server with an OpenAI-compatible `/v1/chat/completions` endpoint. It finds them in `~/.pi/agent/models.json`, the same file Pi uses: one entry per provider, with its address, its key and its models. Run the model with [Ollama](#ollama) on your machine or a shared server, or with [vLLM](#vllm) on a GPU server.

Use another folder with `--agent-dir DIR` (or the `PI_CODING_AGENT_DIR` environment variable), such as a project-local `.pi-agent/`. On Windows the default is `$HOME\.pi\agent\models.json`.

## Ollama

Pull the model and give it a 32k context (Ollama's default of 4096 tokens is too small and cuts requests without an error):

```bash
ollama pull gemma4:12b
printf 'FROM gemma4:12b\nPARAMETER num_ctx 32768\n' > Modelfile
ollama create gemma4-workshop:12b -f Modelfile
```

Add the endpoint to `~/.pi/agent/models.json`, the same file Pi uses. For a shared Ollama server, replace `localhost` with its address:

```json
{
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "models": [
        { "id": "gemma4-workshop:12b", "name": "Gemma 4 12B (32k)", "contextWindow": 32768, "maxTokens": 8192 }
      ]
    }
  }
}
```

For a shared server, start Ollama listening on all interfaces with `OLLAMA_HOST=0.0.0.0:11434 ollama serve`. Ollama has no authentication: anyone who can reach the port can use the model. Keep it on the workshop network, never open on the public internet.

## vLLM

[vLLM](https://docs.vllm.ai) serves models on a GPU server, with the same OpenAI-compatible API. Start it with tool calling on: without `--enable-auto-tool-choice` and a `--tool-call-parser`, vLLM answers in text and never calls a tool. The parser depends on the model family: `hermes` for Qwen, `llama3_json` for Llama 3.x, `mistral` for Mistral.

```bash
vllm serve Qwen/Qwen3-8B --max-model-len 32768 --enable-auto-tool-choice --tool-call-parser hermes
```

Add it to `~/.pi/agent/models.json` next to (or instead of) `ollama`. The `id` is the model name vLLM serves. `apiKey` matters only if you started vLLM with `--api-key`; it can also name an environment variable, such as `"VLLM_API_KEY"`:

```json
{
  "providers": {
    "vllm": {
      "baseUrl": "http://localhost:8000/v1",
      "api": "openai-completions",
      "apiKey": "none",
      "models": [
        { "id": "Qwen/Qwen3-8B", "name": "Qwen3 8B (vLLM)", "contextWindow": 32768, "maxTokens": 8192 }
      ]
    }
  }
}
```

## Choosing and switching models

pi2 starts with the first model in `models.json`. Start with another one with `--model`, as `provider/id`:

```bash
python3 pi2.py -e examples/hello.py --model vllm/Qwen/Qwen3-8B
```

Inside pi2, `/model` lists the models and `/model 2` or `/model <provider/id>` switches. The conversation stays; the next request goes to the new model.

## `contextWindow` and `maxTokens`

- `contextWindow` is how many tokens the model can take. pi2 uses it for the footer's percentage and to decide when to [compact](compaction.md). Set it to what the server really allows: Ollama's `num_ctx`, vLLM's `--max-model-len`. Too high, and requests fail before pi2 compacts; too low, and it compacts early.
- `maxTokens` caps each answer. It is sent with every request.
