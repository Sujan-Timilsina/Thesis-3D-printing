# GPT-5 API Parameter Change

## Important Discovery (October 31, 2025)

**GPT-5 models ARE available in the OpenAI API!**

However, they require a **different parameter** than GPT-4 models:

### Parameter Comparison

| Model Family | Parameter Name | Example |
|--------------|----------------|---------|
| GPT-4.x (old) | `max_tokens` | `max_tokens=2000` |
| GPT-5.x (new) | `max_completion_tokens` | `max_completion_tokens=2000` |

### Available GPT-5 Models

According to OpenAI documentation (as of Oct 2025):
- `gpt-5` - Best model for coding and agentic tasks
- `gpt-5-mini` - Faster, cost-efficient version (what we're using)
- `gpt-5-nano` - Fastest, most cost-efficient
- `gpt-5-pro` - Smarter, more precise responses
- `gpt-5-codex` - Optimized for agentic coding

### Error We Encountered

```
Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.", 'type': 'invalid_request_error', 'param': 'max_tokens', 'code': 'unsupported_parameter'}}
```

### Solution Implemented

We now detect if the model name contains "gpt-5" and use the appropriate parameter:

```python
if "gpt-5" in model_name:
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.7,
        max_completion_tokens=2000  # New parameter for GPT-5
    )
else:
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.7,
        max_tokens=2000  # Old parameter for GPT-4
    )
```

### Benefits of GPT-5-mini

- **Better reasoning** than GPT-4o-mini
- **Vision capabilities** confirmed working
- **Cost-efficient** for production use
- **Faster responses** than full GPT-5

## Testing Status

✅ GPT-5-mini now works correctly with vision API
✅ Falls back to GPT-4o-mini if needed
✅ Code extraction working properly
