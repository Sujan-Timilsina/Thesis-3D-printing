import os
from dotenv import load_dotenv
from openai import OpenAI
import requests
import json
import random

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Backend API URL (we'll make this optional)
BACKEND_URL = "http://localhost:8000"

def extract_openscad_code(text):
    """Extract only the OpenSCAD code from AI response, removing explanatory text"""
    import re
    
    # First, try to find code blocks (marked with ``` or ```openscad)
    code_block_pattern = r'```(?:openscad)?\s*\n(.*?)```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    
    if matches:
        # Return the first code block found
        return matches[0].strip()
    
    # Try to find where actual code starts (after explanatory text)
    # Look for the first line that has OpenSCAD syntax
    lines = text.split('\n')
    code_start_index = -1
    code_end_index = len(lines)
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if this looks like the start of OpenSCAD code
        if code_start_index == -1:
            is_code_start = any([
                stripped.startswith('//'),
                stripped.startswith('/*'),
                stripped.startswith('module '),
                re.match(r'^(cube|cylinder|sphere|translate|rotate|union|difference|intersection|linear_extrude|color)\s*\(', stripped, re.IGNORECASE),
                stripped.startswith('$')  # OpenSCAD special variables
            ])
            
            if is_code_start:
                code_start_index = i
        
        # Check if we've hit explanatory text after code started
        elif stripped and not stripped.startswith('//') and not stripped.startswith('/*'):
            # This looks like a sentence (not code)
            if (len(stripped) > 30 and 
                not any(c in stripped for c in [';', '{', '}', '(', ')', '[', ']']) and
                stripped[0].isupper() and 
                ' ' in stripped):
                code_end_index = i
                break
    
    if code_start_index != -1:
        code_lines = lines[code_start_index:code_end_index]
        extracted = '\n'.join(code_lines).strip()
        if extracted:
            print(f"✂️ Extracted {len(extracted)} chars of OpenSCAD code (removed explanatory text)")
            return extracted
    
    # Last resort: remove common explanatory phrases
    cleaned = text
    phrases_to_remove = [
        r'Here\'s.*?:\s*',
        r'This code.*?\.\s*',
        r'The following.*?:\s*',
        r'I\'ve created.*?\.\s*',
        r'This design.*?\.\s*',
        r'Note:.*?\n',
        r'Important:.*?\n'
    ]
    
    for phrase in phrases_to_remove:
        cleaned = re.sub(phrase, '', cleaned, flags=re.IGNORECASE)
    
    if cleaned != text:
        print(f"✂️ Cleaned explanatory text from response")
        return cleaned.strip()
    
    # If all else fails, return the original text (but warn about it)
    print(f"⚠️ Could not extract OpenSCAD code, returning full response ({len(text)} chars)")
    return text.strip()

def generate_geometry_code(description, image_data=None, dimensions=None):
    """Generate OpenSCAD code for creating 3D geometry"""
    
    # Create a detailed prompt for the AI - VERY explicit about code-only output
    system_prompt = """You are an OpenSCAD code generator. Your ONLY job is to output pure OpenSCAD code.

CRITICAL RULES:
1. Output ONLY OpenSCAD code - no explanations, no descriptions, no markdown
2. Do NOT use code blocks (```) - just raw code
3. Do NOT write "Here's the code" or any introductory text
4. Do NOT add explanations after the code
5. Start immediately with the code (// comments inside code are OK)
6. Every line must be either code or a code comment (//)

Generate valid, executable OpenSCAD code using primitives like cube(), cylinder(), sphere(), translate(), rotate(), etc."""

    if dimensions:
        dim_text = f"\nDimensions:\n- Width: {dimensions['width']}mm\n- Height: {dimensions['height']}mm\n- Depth: {dimensions['depth']}mm"
    else:
        dim_text = ""

    # Build the user prompt - short and direct
    user_prompt = f"""Generate OpenSCAD code for: {description}{dim_text}

REMEMBER: Output ONLY code. No explanations. No markdown. Start with the first line of code."""
    
    # If image data is provided, try to use vision capabilities
    if image_data:
        try:
            import base64
            
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Determine image type
            if image_data.startswith(b'\x89PNG'):
                media_type = "image/png"
            elif image_data.startswith(b'\xff\xd8'):
                media_type = "image/jpeg"
            elif image_data.startswith(b'GIF'):
                media_type = "image/gif"
            elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:20]:
                media_type = "image/webp"
            else:
                media_type = "image/jpeg"  # Default fallback
            
            # Build the data URL for base64 encoded image
            image_data_url = f"data:{media_type};base64,{image_base64}"
            
            # Use vision-enabled message format (CORRECT FORMAT according to OpenAI docs)
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text", 
                            "text": user_prompt + "\n\nImage provided. Analyze the image and generate OpenSCAD code to recreate the object. CODE ONLY - no descriptions."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url,
                                "detail": "high"  # Use high detail for better vision analysis
                            }
                        }
                    ]
                }
            ]
            
            # Try vision models in order of preference
            # GPT-5-mini first for quality (even though it sometimes returns 0 chars - we'll retry)
            models_to_try = [
                ("gpt-5-mini", "GPT-5-mini"),      # Best quality (newest model) - priority despite unreliability
                ("gpt-4o-mini", "GPT-4o-mini")     # Fallback if GPT-5-mini fails
            ]
            
            generated_code = None  # Initialize outside the loop
            successful_model = None
            
            for model_name, model_label in models_to_try:
                try:
                    print(f"🔍 Trying {model_label} for image analysis...")
                    
                    # GPT-5 models have different requirements
                    if "gpt-5" in model_name:
                        # Try Responses API if available (newer SDK), otherwise skip GPT-5 for vision
                        if hasattr(client, 'responses'):
                            # Use Responses API for GPT-5 vision
                            response = client.responses.create(
                                model=model_name,
                                input=[
                                    {
                                        "type": "message",
                                        "role": "system",
                                        "content": [{"type": "input_text", "text": system_prompt}]
                                    },
                                    {
                                        "type": "message",
                                        "role": "user",
                                        "content": [
                                            {"type": "input_text", "text": user_prompt + "\n\nImage provided. Analyze the image and generate OpenSCAD code to recreate the object. CODE ONLY - no descriptions."},
                                            {"type": "input_image", "image_url": image_data_url}
                                        ]
                                    }
                                ],
                                max_output_tokens=2000
                            )
                            
                            # Get the output text
                            generated_code = response.output_text
                            print(f"📝 {model_label} raw response length: {len(generated_code)} chars")

                        else:
                            # SDK too old for Responses API - skip GPT-5 for vision
                            print(f"⚠️ {model_label} requires Responses API (SDK too old), skipping...")
                            raise Exception(f"{model_label} requires newer SDK for vision support")
                    else:
                        # GPT-4: Use Chat Completions API (supports vision)
                        response = client.chat.completions.create(
                            model=model_name,
                            messages=messages,
                            temperature=0.7,
                            max_tokens=2000
                        )
                        generated_code = response.choices[0].message.content
                        print(f"📝 {model_label} raw response length: {len(generated_code)} chars")
                    
                    # Check if the response indicates vision actually worked (BEFORE code extraction)
                    if "unable to view" in generated_code.lower() or "cannot see" in generated_code.lower() or "can't see" in generated_code.lower():
                        print(f"⚠️ {model_label} returned but couldn't process image")
                        raise Exception(f"{model_label} couldn't process image")
                    
                    # Extract only OpenSCAD code (do this AFTER vision validation)
                    generated_code = extract_openscad_code(generated_code)
                    
                    # Check if extraction resulted in empty code
                    if not generated_code or len(generated_code.strip()) < 10:
                        print(f"⚠️ {model_label} returned empty code after extraction")
                        raise Exception(f"{model_label} returned empty code")
                    
                    successful_model = model_label
                    print(f"✅ Successfully used {model_label} to analyze image!")
                    break  # Success! Exit the loop
                    
                except Exception as model_error:
                    print(f"❌ {model_label} failed: {str(model_error)}")
                    if model_name == models_to_try[-1][0]:  # Last model in list
                        raise Exception("All vision models failed")
                    continue  # Try next model
            
            if not generated_code:
                raise Exception("No vision model could process the image")
                
        except Exception as image_error:
            print(f"❌ Image processing failed: {str(image_error)}")
            print("🔄 Falling back to text-only with enhanced description...")
            
            # Fallback to text-only with enhanced prompt
            enhanced_prompt = user_prompt + f"""
            
            NOTE: An image was uploaded but vision analysis is not available with your current OpenAI plan. 
            Please create a detailed OpenSCAD model based on the description: "{description}"
            Make reasonable assumptions about the shape and structure.
            Add comments explaining your design decisions.
            """
            
            # Use GPT-4o-mini for text-only fallback (more reliable than GPT-5-mini without Responses API)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            generated_code = response.choices[0].message.content
            generated_code = extract_openscad_code(generated_code)
    else:
        # No image provided, use standard text processing
        # Use GPT-4o-mini for consistency (works well for text-only)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        generated_code = response.choices[0].message.content
        generated_code = extract_openscad_code(generated_code)
    
    
    # Generate a simple model ID (backend not used)
    model_id = str(random.randint(10000, 99999))
    
    return generated_code, model_id

def refine_geometry_code(model_id, refinement_request, dimensions=None, original_code=None):
    """Refine existing geometry code based on user requests"""
    
    # Use the provided original code (backend not used)
    existing_code = original_code
    
    if not existing_code:
        return None, None
    
    system_prompt = """You are an expert in 3D modeling and OpenSCAD code refinement.
    Modify the existing code according to the requested changes while maintaining code quality and structure."""
    
    user_prompt = f"""Original OpenSCAD code:
    {existing_code}
    
    Requested changes: {refinement_request}
    
    If provided, apply these dimensions:
    {json.dumps(dimensions) if dimensions else 'No new dimensions provided'}
    
    Requirements:
    1. Maintain the basic structure of the code
    2. Implement the requested changes
    3. Update comments to reflect changes
    4. Keep the code modular and parameterized
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fixed: Using model you have access to
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        refined_code = response.choices[0].message.content
        
        # Try to update in backend if available
        try:
            if model_id:
                update_model(model_id, {
                    "code": refined_code,
                    "metadata": {
                        "dimensions": dimensions,
                        "refined": True,
                        "code_type": "openscad"
                    }
                })
        except:
            print("Backend not available for update")
        
        return refined_code, model_id
    except Exception as e:
        print(f"Error in OpenAI API call: {str(e)}")
        return None, None

def store_model(model_data):
    """Store model in backend (optional)"""
    try:
        response = requests.post(f"{BACKEND_URL}/models/", json=model_data, timeout=2)
        if response.ok:
            return response.json()["id"]
    except Exception as e:
        # Silently fail - backend is optional
        pass
    return None

def update_model(model_id, model_data):
    """Update model in backend (optional)"""
    try:
        response = requests.put(f"{BACKEND_URL}/models/{model_id}", json=model_data, timeout=5)
        return response.ok
    except Exception as e:
        print(f"Could not update model: {str(e)}")
        return False

def get_model(model_id):
    """Retrieve model from backend (optional)"""
    try:
        response = requests.get(f"{BACKEND_URL}/models/{model_id}", timeout=5)
        if response.ok:
            return response.json()
    except Exception as e:
        print(f"Could not retrieve model: {str(e)}")
    return None