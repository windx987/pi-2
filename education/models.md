# Connect a model

Pi reads its models from `~/.pi/agent/models.json`. The workshop runs Gemma 4 through [Ollama](#ollama), on your machine or on a shared server. [vLLM](#vllm) works the same way on a GPU server, and so does [any provider Pi supports](#other-providers).

## Ollama

Ollama serves an OpenAI-compatible endpoint, so the model can run on your machine or on a shared server:

| Ollama runs on | `baseUrl` in `models.json` |
|---|---|
| Your machine | `http://localhost:11434/v1` |
| A shared workshop server | `http://<server-ip>:11434/v1` |

On the machine that runs Ollama, pull the model and give it a 32k context (Ollama's default of 4096 tokens is too small for Pi and cuts requests without an error):

```bash
ollama pull gemma4:12b                       # gemma4:31b needs about 20 GB of free memory
printf 'FROM gemma4:12b\nPARAMETER num_ctx 32768\n' > Modelfile
ollama create gemma4-workshop:12b -f Modelfile
```

For a shared server, start Ollama listening on all interfaces with `OLLAMA_HOST=0.0.0.0:11434 ollama serve`. Ollama has no authentication: anyone who can reach the port can use the model. Keep the server on the workshop network or behind a firewall that allows only participants' addresses, never open on the public internet.

On each participant's machine, add the endpoint to `~/.pi/agent/models.json`, with `localhost` replaced by the server's address when you use a shared server:

```json
{
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "compat": { "supportsDeveloperRole": false },
      "models": [
        { "id": "gemma4-workshop:12b", "name": "Gemma 4 12B (32k)", "contextWindow": 32768, "maxTokens": 8192 }
      ]
    }
  }
}
```

Check the endpoint, then start Pi from source with that model:

```bash
curl http://localhost:11434/v1/models          # lists gemma4-workshop:12b
./pi-test.sh --model ollama/gemma4-workshop:12b
```

## vLLM

[vLLM](https://docs.vllm.ai) serves models on a GPU server with the same OpenAI-compatible API. Start it with tool calling on: without `--enable-auto-tool-choice` and a `--tool-call-parser`, vLLM answers in text and never calls a tool. The parser depends on the model family: `hermes` for Qwen, `llama3_json` for Llama 3.x, `mistral` for Mistral.

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
      "compat": { "supportsDeveloperRole": false },
      "models": [
        { "id": "Qwen/Qwen3-8B", "name": "Qwen3 8B (vLLM)", "contextWindow": 32768, "maxTokens": 8192 }
      ]
    }
  }
}
```

Then start with `./pi-test.sh --model vllm/Qwen/Qwen3-8B`.

## Other providers

Any other provider Pi supports works too: run `./pi-test.sh` and `/login`, or set an API key such as `ANTHROPIC_API_KEY`. Setup details are in [exercises/README.md](exercises/README.md).

## `contextWindow` and `maxTokens`

- `contextWindow` is how many tokens the model can take. Pi uses it for the footer's percentage and to decide when to compact (see [core.md](architecture/core.md#compaction)). Set it to what the server really allows: Ollama's `num_ctx`, vLLM's `--max-model-len`.
- `maxTokens` caps each answer.
