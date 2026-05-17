# GPT-5-mini Vision Support - Investigation Results

## Problem
GPT-5-mini was returning completely empty responses (0 characters) when called with image inputs via the Chat Completions API (`client.chat.completions.create()`).

## Root Cause
**GPT-5 models require the Responses API for vision/multimodal support**, which is **NOT yet available in the Python SDK** (as of version 2.6.1).

### Key Findings:

1. **OpenAI Documentation shows GPT-5-mini DOES support vision:**
   - Vision guide confirms image support (1.62x token multiplier)
   - Modalities listed: ✅ Text, ✅ Image (input only)

2. **BUT the Responses API is NOT in the SDK yet:**
   - `client.responses` attribute doesn't exist in openai 2.6.1
   - Vision examples in docs use Responses API which isn't available
   - This is a gap between API availability and SDK support

3. **Chat Completions API doesn't work for GPT-5 vision:**
   - Returns empty responses when images are provided
   - Parameters like `extra_body={"max_completion_tokens": ...}` don't help

## Current Solution

**Use GPT-4o-mini for vision tasks** (fully supported in current SDK):

```python
# GPT-4o-mini works perfectly with Chat Completions API
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "System prompt"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "User prompt"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
            ]
        }
    ],
    temperature=0.7,
    max_tokens=2000
)
```

## Future Solution (when SDK updated)

Once the OpenAI Python SDK adds Responses API support, GPT-5-mini vision will work:

```python
# This will work once client.responses is added to SDK
if hasattr(client, 'responses'):
    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {
                "type": "message",
                "role": "system",
                "content": [{"type": "input_text", "text": "System prompt"}]
            },
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "User prompt"},
                    {"type": "input_image", "image_url": "data:image/png;base64,..."}
                ]
            }
        ],
        max_output_tokens=2000
    )
    generated_code = response.output_text
```

## Implementation

The code now:
1. ✅ Checks if `client.responses` exists before trying GPT-5
2. ✅ Falls back to GPT-4o-mini for vision (works reliably)
3. ✅ Uses GPT-4o-mini for text-only as well (consistent behavior)
4. ✅ Skips GPT-5-mini for vision until SDK supports Responses API

## Model Priority for Vision

Current working order:
1. **GPT-4o-mini** - Works perfectly with Chat Completions API ✅
2. **GPT-4o** - Works (more expensive but available)
3. **GPT-4-turbo** - Works (older but reliable)
4. ~~GPT-5-mini~~ - Skipped until SDK supports Responses API ⏳

## References

- OpenAI Vision Guide: https://platform.openai.com/docs/guides/images-vision
- GPT-5 Usage Guide: https://platform.openai.com/docs/guides/latest-model
- Responses API Reference: https://platform.openai.com/docs/api-reference/responses
- SDK Issue: Responses API not yet in Python SDK 2.6.1
