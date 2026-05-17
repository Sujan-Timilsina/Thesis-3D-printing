import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import random
import re
import base64
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize Gemini client (lazy - only when used)
_gemini_model = None
_gemini_framework_hash = None

def _get_gemini_model():
    global _gemini_model, _gemini_framework_hash
    fw_hash = hash(CADQUERY_FRAMEWORK)
    if _gemini_model is None or _gemini_framework_hash != fw_hash:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        _gemini_model = genai.GenerativeModel(
            model_name="gemini-3.1-pro-preview",
            system_instruction=CADQUERY_FRAMEWORK,
        )
        _gemini_framework_hash = fw_hash
    return _gemini_model

# ================================================================
#  Phase-specific system prompts (sent instead of the full framework)
# ================================================================
FRAMEWORK_CORE = r"""You are an expert CadQuery programmer and engineering assistant.

At the start of EVERY response, display: PHASE X - <PHASE NAME>

CRITICAL RULES:
- Output EXACTLY ONE phase per response. Never combine phases. Stop and wait after each phase.
- Phases ONLY move forward. Never repeat a completed phase. Never output PHASE 1 twice.
- Use right-handed coordinates: +X=Right, +Y=Forward, +Z=Up. Origin must be a physical point on the part.
"""

PHASE_PROMPTS = {
    1: FRAMEWORK_CORE + r"""
You are in PHASE 1 - REQUEST ANALYSIS.
Identify: input type, user intent, dimensions, geometric structure, feasibility.
If a drawing is provided, extract dimensions and classify as EXPLICIT / INFERABLE / UNKNOWN.
Ask minimal clarification questions if info is missing. Keep questions concrete and short.
Goal: full parametric characterization of the part.
STAY IN PHASE 1: If the user provides feedback, corrections, or additional info, incorporate it and respond with an UPDATED Phase 1 analysis. Only advance to Phase 2 when the user explicitly says to confirm or proceed.""",

    2: FRAMEWORK_CORE + r"""
You are in PHASE 2 - CONSOLIDATED UNDERSTANDING CONFIRMATION.
Present a consolidated understanding: geometry, sub-shapes, dimension list, assumptions, coordinate frame, origin.
STAY IN PHASE 2: Any user message that is NOT exactly "Generate Plan" is feedback. Update your understanding and present Phase 2 again. Only the exact command "Generate Plan" moves forward to Phase 3.""",

    3: FRAMEWORK_CORE + r"""
You are in PHASE 3 - PLAN GENERATION. Triggered by "Generate Plan".
Build: sub-shape decomposition, sketch planes, extrusion directions, operation ordering, attachment logic.
Run internal checks: delta_end=0, delta_attach=0, residuals=0. Plan is hidden by default.
Return: "Generation plan ready. Internal checks passed. Ready for code generation."
User can say "Show Plan" / "Show Checks" / "Show Both".
STAY IN PHASE 3: If the user provides feedback on the plan, update it and respond with Phase 3 again. Only the exact command "Generate Code" advances to Phase 4.""",

    4: FRAMEWORK_CORE + r"""
You are in PHASE 4 - CODE GENERATION. Triggered by "Generate Code".
Follow the plan EXACTLY. No optimizations or reordering.
For straight-edge profiles: use Workplane().polyline(PTS).close(), Face.makeFromWires(wire), then extrude.
Never extrude wires directly. All extrusions from Face.makeFromWires().
Chamfer tolerance: C_used = C_spec - 0.001 mm.
CRITICAL: The final CadQuery object MUST be assigned to a variable named `result`. Example: result = housing.clean()
Do NOT use show_object(). Do NOT use cq.exporters.export(). Do NOT assign to any other variable name as the final output.
Code must: import cadquery as cq, be fully parametric, assign final shape to `result`, be in a ```python block.
STAY IN PHASE 4: When the user requests changes, edits, or fixes, ALWAYS respond with "PHASE 4 - CODE GENERATION" and provide the updated complete code. NEVER go back to Phase 1, 2, or 3. Apply the requested changes directly to the existing code and output the full updated script."""
}

def _get_phase_prompt(current_phase):
    """Return the appropriate system prompt for the current phase."""
    phase = max(1, min(current_phase, 4))
    return PHASE_PROMPTS.get(phase, PHASE_PROMPTS[1])

# Max output tokens per phase (lower for cheaper early phases)
PHASE_MAX_TOKENS = {1: 30000, 2: 30000, 3: 30000, 4: 30000}
CADQUERY_FRAMEWORK = r"""
ROLE

You are an expert CadQuery programmer and engineering assistant.

Your task is to generate correct, parametric CadQuery geometry through a structured multi-phase interaction with the user.

The system prioritizes correctness, determinism, watertight geometry construction, and structured human-AI collaboration over autonomy or speed.

At the start of EVERY response, display:

PHASE X - <PHASE NAME>

Never omit the phase label.

CRITICAL RULE: You must output EXACTLY ONE phase per response. Never combine multiple phases in a single response. After outputting one phase, STOP and wait for the user's reply before proceeding to the next phase. For example, do NOT output Phase 1 and Phase 2 together. Each phase requires user confirmation or input before advancing.

CRITICAL RULE: Phases ONLY move forward, never backward. Once you have completed Phase 1 and asked your clarification questions, your NEXT response MUST be Phase 2 (or higher). You must NEVER output "PHASE 1" more than once in a session. If the user answers your Phase 1 questions, move to Phase 2. If images are attached, still move forward. Do NOT re-analyse or repeat Phase 1 under any circumstance.


====================================================================
GLOBAL COORDINATE FRAME REQUIREMENT (MANDATORY)
====================================================================

A standard right-handed coordinate system must always be used:

+X = Right
+Y = Forward
+Z = Up

The origin (0,0,0) must always be explicitly defined as a physical point on the part.

Examples:
- bottom-left corner of base plate
- center of bottom face
- bounding box lower corner

The origin must remain fixed throughout the entire modelling session.

All geometry placement must be expressed in global coordinates or relative to previously defined faces whose coordinates are explicitly known.


====================================================================
PHASE 1 - REQUEST ANALYSIS
====================================================================

A session begins with user input.

The model identifies:
- input type (text, image, or both)
- user intent
- available dimensions
- geometric structure
- modelling feasibility

If a technical drawing is provided:

Extract as many explicit dimensions as possible.

Classify each dimension:
EXPLICIT
INFERABLE (must be stated as assumption)
UNKNOWN

Organize extracted parameters into:
- overall dimensions
- feature dimensions
- feature locations
- depths / thicknesses
- angles
- tolerances / notes

Do NOT assume missing geometry.

If required information is missing:
Ask minimal, precise clarification questions.

Questions must:
- be concrete
- be answerable quickly
- avoid overwhelming the user

The goal of Phase 1 is full parametric characterization of the part.


====================================================================
PHASE 2 - CONSOLIDATED UNDERSTANDING CONFIRMATION
====================================================================

The model presents a consolidated understanding of:
- geometry
- sub-shapes
- modelling intent
- dimension list
- assumptions
- unknowns (if any)
- coordinate frame orientation
- physical meaning of origin (0,0,0)

User interaction rules:

Only the command

Generate Plan

moves the session forward.

Any other message is interpreted as feedback.

The model updates understanding accordingly.


====================================================================
PHASE 3 - PLAN GENERATION
====================================================================

Triggered ONLY by:

Generate Plan


This phase constructs the internal generation strategy.

The generation plan includes:
- sub-shape decomposition
- sketch geometry definitions
- sketch planes
- extrusion directions
- operation ordering
- attachment logic
- coordinate predictions


--------------------------------------------------------------------
INTERNAL MATHEMATICAL CHECKS (MANDATORY)
--------------------------------------------------------------------

For every extrusion:

Axis_end_pred = Axis_start + D

Require:

delta_end = Axis_end_pred - Axis_end_expected = 0


For every attachment between solids:

delta_attach = Plane_A - Plane_B = 0


For placement intent validation:

Flush / centered / offset relationships must be written as coordinate equations

Require:

Residual = 0


If any equation:
cannot be formed
is undefined
!= 0

then the plan is invalid.


--------------------------------------------------------------------
PLAN VISIBILITY RULE
--------------------------------------------------------------------

The generation plan is hidden by default.

Return:

Generation plan ready.
Internal checks passed (delta_end=0, delta_attach=0, residuals=0).
Ready for code generation.

User commands:

Show Plan
Show Checks
Show Both


--------------------------------------------------------------------
PLAN VALIDATION RULE
--------------------------------------------------------------------

Code generation is only allowed if:

ALL internal checks equal 0.


User must explicitly send:

Generate Code


Any other message triggers plan revision.


====================================================================
PHASE 4 - CODE GENERATION
====================================================================

Triggered ONLY by:

Generate Code


The generated code must follow EXACTLY the generation plan.

No optimizations allowed.
No operation reordering allowed.
No geometry reinterpretation allowed.


--------------------------------------------------------------------
MANDATORY PROFILE CONSTRUCTION PROTOCOL
--------------------------------------------------------------------

For profiles containing straight edges:

ALWAYS use:

wire  = Workplane(PLANE).polyline(PTS).close().objects[0]
face  = Face.makeFromWires(wire)
solid = Workplane(PLANE).newObject([face]).extrude(D)


Rules:

PTS must contain explicit coordinates.

Profiles must be closed.

Extrusions must always originate from faces.

Wire extrusion is forbidden.


--------------------------------------------------------------------
FACE CREATION RULE
--------------------------------------------------------------------

Every extrusion must originate from:

Face.makeFromWires(wire)

Never extrude wires directly.


--------------------------------------------------------------------
WATERTIGHT GEOMETRY REQUIREMENT
--------------------------------------------------------------------

Sub-parts must attach exactly:

Plane_A - Plane_B = 0


Floating geometry is forbidden.


--------------------------------------------------------------------
CHAMFER TOLERANCE RULE
--------------------------------------------------------------------

For round chamfers:

C_used = C_spec - 0.001 mm


This adjustment is mandatory.

Reason:
Prevents geometric kernel edge-selection instability.


--------------------------------------------------------------------
CODE REQUIREMENTS
--------------------------------------------------------------------

Generated CadQuery code must be:
- fully parametric
- coordinate-consistent
- watertight
- deterministic
- commented per operation step
- aligned with generation plan order

The code MUST:
1. Import cadquery: import cadquery as cq
2. Use the CadQuery Workplane API
3. Store the final result in a variable called 'result'
4. The 'result' must be a CadQuery Workplane or Shape object
5. Wrap the code in a ```python code block


--------------------------------------------------------------------
REVISION LOOP
--------------------------------------------------------------------

If user rejects geometry:

Model returns to appropriate earlier phase:
Phase 2 -> misunderstanding
Phase 3 -> incorrect plan
Phase 4 -> execution error


If execution error occurs:

Perform debugging and regenerate corrected code.


Session completes once user accepts geometry.
"""


def _trim_to_valid_python(code):
    """Trim trailing non-Python prose that the AI may append after the code."""
    lines = code.split('\n')
    # Binary-search from the end: try compiling progressively shorter slices
    best = len(lines)
    for end in range(len(lines), 0, -1):
        snippet = '\n'.join(lines[:end])
        try:
            compile(snippet, '<check>', 'exec')
            best = end
            break
        except SyntaxError:
            continue
    trimmed = '\n'.join(lines[:best]).strip()
    return trimmed if trimmed else code


def extract_cadquery_code(text):
    """Extract CadQuery/Python code from AI response text."""
    # Try to find code blocks (marked with ``` or ```python)
    code_block_pattern = r'```(?:python)?\s*\n(.*?)```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)

    if matches:
        # Return the longest code block (most likely the full CadQuery code)
        code = max(matches, key=len).strip()
        return _trim_to_valid_python(code)

    # Try to find lines that look like Python code
    lines = text.split('\n')
    code_start = -1
    code_end = len(lines)

    for i, line in enumerate(lines):
        stripped = line.strip()
        if code_start == -1:
            is_code = any([
                stripped.startswith('#'),
                stripped.startswith('import '),
                stripped.startswith('from '),
                re.match(r'^(result|solid|wire|face|model)\s*=', stripped),
                stripped.startswith('def '),
            ])
            if is_code:
                code_start = i
        elif stripped and not stripped.startswith('#'):
            if (len(stripped) > 40
                and not any(c in stripped for c in ['=', '(', ')', '[', ']', '.'])
                and stripped[0].isupper()
                and ' ' in stripped):
                code_end = i
                break

    if code_start != -1:
        extracted = '\n'.join(lines[code_start:code_end]).strip()
        if extracted and len(extracted) > 10:
            return _trim_to_valid_python(extracted)

    return None


def detect_phase(text):
    """Detect which phase the AI response is in."""
    match = re.search(r'PHASE\s+(\d)\s*[-\u2013\u2014]\s*(.+)', text, re.IGNORECASE)
    if match:
        return int(match.group(1)), match.group(2).strip()
    return None, None


def has_cadquery_code(text):
    """Check if the AI response contains CadQuery code."""
    code = extract_cadquery_code(text)
    if code and ('cadquery' in code.lower() or 'import cq' in code.lower()):
        return True
    return False


def _prepare_history(conversation_history, current_phase):
    """
    Optimize conversation history to reduce token usage:
    1. Only include images in the LAST user message (images are huge)
    2. Summarize completed phase messages into a compact recap
    """
    if not conversation_history:
        return []

    # Find the last user message index (the one that gets to keep images)
    last_user_idx = None
    for i in range(len(conversation_history) - 1, -1, -1):
        if conversation_history[i]["role"] == "user":
            last_user_idx = i
            break

    # Separate messages by phase
    current_phase_msgs = []
    old_phase_summaries = []
    prev_phase = None

    for i, msg in enumerate(conversation_history):
        msg_phase = msg.get("phase", 1)

        # Collect messages from completed phases into summaries
        if msg_phase < current_phase:
            if msg_phase != prev_phase:
                # Start a new phase summary
                if prev_phase is not None and old_phase_summaries:
                    pass  # already appended
                old_phase_summaries.append({"phase": msg_phase, "texts": []})
                prev_phase = msg_phase
            # Add just the text (no images) to summary
            role_label = "User" if msg["role"] == "user" else "AI"
            # Truncate long messages in summaries
            content = msg["content"]
            if len(content) > 500:
                content = content[:500] + "..."
            old_phase_summaries[-1]["texts"].append(f"{role_label}: {content}")
        else:
            # Current phase: include full message, but strip images from non-last messages
            cleaned = {"role": msg["role"], "content": msg["content"]}
            if i == last_user_idx and "images" in msg:
                cleaned["images"] = msg["images"]
            current_phase_msgs.append(cleaned)

    # Build optimized history
    optimized = []

    # Add a compact summary of completed phases
    if old_phase_summaries:
        summary_parts = []
        for ps in old_phase_summaries:
            summary_parts.append(f"[Phase {ps['phase']} summary]\n" + "\n".join(ps["texts"][-4:]))  # Keep last 4 exchanges per phase
        optimized.append({
            "role": "user",
            "content": "[CONTEXT FROM PREVIOUS PHASES - do not repeat these phases]\n" + "\n\n".join(summary_parts)
        })
        optimized.append({
            "role": "assistant",
            "content": f"Understood. I have the context from previous phases. Continuing from Phase {current_phase}."
        })

    # Add current phase messages
    optimized.extend(current_phase_msgs)

    return optimized


def _chat_gemini(conversation_history, image_data=None, current_phase=1):
    """Send a conversational message to Gemini using the CadQuery framework."""
    from PIL import Image
    import io

    # Try the new google-genai SDK first (better thinking support),
    # fall back to the older google.generativeai SDK.
    try:
        from google import genai as genai_new
        from google.genai import types as genai_types
        return _chat_gemini_new_sdk(conversation_history, image_data, current_phase,
                                     genai_new, genai_types)
    except ImportError:
        pass

    # Fallback: older google.generativeai SDK
    import google.generativeai as genai
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    phase_prompt = _get_phase_prompt(current_phase)
    model = genai.GenerativeModel(
        model_name="gemini-3.1-pro-preview",
        system_instruction=phase_prompt,
    )

    optimized = _prepare_history(conversation_history, current_phase)

    # Build Gemini content list
    contents = []
    for msg in optimized:
        role = "user" if msg["role"] == "user" else "model"
        parts = [msg["content"]]

        if "images" in msg and msg["images"]:
            for img_bytes in msg["images"]:
                img = Image.open(io.BytesIO(img_bytes))
                parts.append(img)

        contents.append({"role": role, "parts": parts})

    max_tokens = PHASE_MAX_TOKENS.get(current_phase, 30000)

    try:
        for attempt in range(4):
            try:
                response = model.generate_content(
                    contents,
                    generation_config=genai.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=0.2,
                    ),
                )
                # Check for truncation
                if response.candidates and response.candidates[0].finish_reason.name == 'MAX_TOKENS':
                    print(f"[DEBUG] WARNING: Gemini response truncated at {max_tokens} tokens")
                # Extract token usage from response metadata
                usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "thinking_tokens": 0, "model": "gemini-3.1-pro-preview"}
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    um = response.usage_metadata
                    usage["prompt_tokens"] = getattr(um, 'prompt_token_count', 0) or 0
                    usage["completion_tokens"] = getattr(um, 'candidates_token_count', 0) or 0
                    usage["total_tokens"] = getattr(um, 'total_token_count', 0) or 0
                return response.text, usage
            except Exception as e:
                if '503' in str(e) and attempt < 3:
                    wait = 2 ** attempt
                    print(f"[DEBUG] Gemini 503 error, retrying in {wait}s (attempt {attempt+1}/4)")
                    time.sleep(wait)
                    continue
                raise
    except Exception as e:
        return f"Error communicating with Gemini: {e}", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "thinking_tokens": 0, "model": "gemini-3.1-pro-preview"}


def _chat_gemini_new_sdk(conversation_history, image_data, current_phase, genai_new, genai_types):
    """Gemini via the new google-genai SDK with explicit thinking support."""
    from PIL import Image
    import io

    client = genai_new.Client(api_key=os.getenv('GEMINI_API_KEY'))
    phase_prompt = _get_phase_prompt(current_phase)
    optimized = _prepare_history(conversation_history, current_phase)

    # Build content list
    contents = []
    for msg in optimized:
        role = "user" if msg["role"] == "user" else "model"
        parts = [genai_types.Part.from_text(text=msg["content"])]

        if "images" in msg and msg["images"]:
            for img_bytes in msg["images"]:
                parts.append(genai_types.Part.from_bytes(
                    data=img_bytes,
                    mime_type="image/jpeg",
                ))

        contents.append(genai_types.Content(role=role, parts=parts))

    max_tokens = PHASE_MAX_TOKENS.get(current_phase, 30000)

    for attempt in range(4):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-pro-preview",
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    system_instruction=phase_prompt,
                    max_output_tokens=max_tokens,
                    temperature=0.2,
                    thinking_config=genai_types.ThinkingConfig(thinking_level="medium"),
                ),
            )

            # Check for truncation
            if response.candidates and response.candidates[0].finish_reason and \
               response.candidates[0].finish_reason.name == 'MAX_TOKENS':
                print(f"[DEBUG] WARNING: Gemini response truncated at {max_tokens} tokens")

            # Extract token usage
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "thinking_tokens": 0, "model": "gemini-3.1-pro-preview"}
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                um = response.usage_metadata
                usage["prompt_tokens"] = getattr(um, 'prompt_token_count', 0) or 0
                usage["completion_tokens"] = getattr(um, 'candidates_token_count', 0) or 0
                usage["total_tokens"] = getattr(um, 'total_token_count', 0) or 0
                usage["thinking_tokens"] = getattr(um, 'thoughts_token_count', 0) or 0

            return response.text, usage
        except Exception as e:
            if '503' in str(e) and attempt < 3:
                wait = 2 ** attempt
                print(f"[DEBUG] Gemini 503 error, retrying in {wait}s (attempt {attempt+1}/4)")
                time.sleep(wait)
                continue
            raise


def chat_with_framework(conversation_history, image_data=None, provider="openai", current_phase=1):
    """
    Send a conversational message using the CadQuery engineering framework.
    
    conversation_history: list of dicts with 'role' and 'content' keys,
                          optionally 'images' (list of bytes).
    image_data: optional list of image bytes for the latest message.
    provider: 'openai' or 'gemini'
    current_phase: current phase number (1-4) for prompt optimization
    
    Returns: AI response text (str)
    """
    if provider == "gemini":
        result = _chat_gemini(conversation_history, image_data, current_phase)
        if isinstance(result, tuple):
            return result  # (text, usage)
        return result, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "thinking_tokens": 0, "model": "gemini"}

    # Use phase-specific system prompt instead of full framework
    system_prompt = _get_phase_prompt(current_phase)
    optimized = _prepare_history(conversation_history, current_phase)
    max_tokens = PHASE_MAX_TOKENS.get(current_phase, 3000)

    # Build messages
    messages = [{"role": "system", "content": system_prompt}]

    for msg in optimized:
        role = "user" if msg["role"] == "user" else "assistant"

        if "images" in msg and msg["images"]:
            # Multimodal message with images — use detail:low for cost savings
            parts = [{"type": "text", "text": msg["content"]}]
            for img_bytes in msg["images"]:
                if img_bytes[:4] == b'\x89PNG':
                    mtype = "image/png"
                elif img_bytes[:2] == b'\xff\xd8':
                    mtype = "image/jpeg"
                else:
                    mtype = "image/jpeg"
                parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mtype};base64,{base64.b64encode(img_bytes).decode()}",
                        "detail": "low",
                    },
                })
            messages.append({"role": role, "content": parts})
        else:
            messages.append({"role": role, "content": msg["content"]})

    # Try gpt-5-mini via Responses API first, then fall back to Chat API
    MAX_RETRIES = 2
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if hasattr(client, 'responses'):
                # Convert messages to Responses API format
                input_msgs = []
                for m in messages:
                    if m["role"] == "system":
                        input_msgs.append({
                            "type": "message",
                            "role": "system",
                            "content": [{"type": "input_text", "text": m["content"]}],
                        })
                    elif isinstance(m["content"], list):
                        # Multimodal
                        text_type = "output_text" if m["role"] == "assistant" else "input_text"
                        parts = []
                        for part in m["content"]:
                            if part["type"] == "text":
                                parts.append({"type": text_type, "text": part["text"]})
                            elif part["type"] == "image_url":
                                parts.append({
                                    "type": "input_image",
                                    "image_url": part["image_url"]["url"],
                                })
                        input_msgs.append({
                            "type": "message",
                            "role": m["role"],
                            "content": parts,
                        })
                    else:
                        # Use output_text for assistant messages, input_text for user messages
                        text_type = "output_text" if m["role"] == "assistant" else "input_text"
                        input_msgs.append({
                            "type": "message",
                            "role": m["role"],
                            "content": [{"type": text_type, "text": m["content"]}],
                        })

                response = client.responses.create(
                    model="gpt-5-mini",
                    input=input_msgs,
                    max_output_tokens=max_tokens,
                )
                # Extract token usage from Responses API
                usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "thinking_tokens": 0, "model": "gpt-5-mini"}
                if hasattr(response, 'usage') and response.usage:
                    usage["prompt_tokens"] = getattr(response.usage, 'input_tokens', 0) or 0
                    usage["completion_tokens"] = getattr(response.usage, 'output_tokens', 0) or 0
                    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
                return response.output_text, usage

        except Exception as e:
            print(f"Responses API attempt {attempt} failed: {e}")
            if attempt == MAX_RETRIES:
                break

    # Fallback: Chat Completions API with gpt-4o-mini
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens,
        )
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "thinking_tokens": 0, "model": "gpt-4o-mini"}
        if resp.usage:
            usage["prompt_tokens"] = resp.usage.prompt_tokens or 0
            usage["completion_tokens"] = resp.usage.completion_tokens or 0
            usage["total_tokens"] = resp.usage.total_tokens or 0
        return resp.choices[0].message.content, usage
    except Exception as e:
        return f"Error communicating with AI: {e}", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "thinking_tokens": 0, "model": "gpt-4o-mini"}


# ================================================================
#  Legacy functions (kept for backward compatibility)
# ================================================================

def extract_openscad_code(text):
    """Extract Python code from AI response (legacy)."""
    return extract_cadquery_code(text) or text.strip()


def generate_geometry_code(description, image_data=None, dimensions=None):
    """Legacy: one-shot code generation. Now redirects through framework."""
    history = [{"role": "user", "content": description}]
    if image_data:
        history[0]["images"] = image_data if isinstance(image_data, list) else [image_data]
    resp, _usage = chat_with_framework(history)
    code = extract_cadquery_code(resp)
    model_id = str(random.randint(10000, 99999))
    return code or resp, model_id


def refine_geometry_code(model_id, refinement_request, dimensions=None, original_code=None):
    """Legacy: code refinement. Now redirects through framework."""
    history = []
    if original_code:
        history.append({"role": "assistant", "content": f"```python\n{original_code}\n```"})
    history.append({"role": "user", "content": refinement_request})
    resp, _usage = chat_with_framework(history)
    code = extract_cadquery_code(resp)
    return code or resp, model_id
