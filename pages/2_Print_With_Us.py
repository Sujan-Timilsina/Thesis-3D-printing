# Print With Us - Professional 3D Printing Service
import streamlit as st
import time
import os
import tempfile
from pathlib import Path
import sys
import subprocess
import json

from auth import require_login
from styles import inject_global_styles

# Page config
st.set_page_config(
    page_title="Print With Us",
    layout="wide"
)

require_login()
inject_global_styles()

# CSS — shared palette (matches Home.py and page 1)
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    *, html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
    }

    /* Hide sidebar and all toggle buttons */
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarNav"],
    header[data-testid="stHeader"],
    button[kind="headerNoPadding"],
    .stSidebar,
    .stSidebarCollapsedControl,
    #stSidebarCollapsedControl,
    [class*="SidebarCollapsed"],
    [class*="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
        z-index: -1 !important;
    }

    .page-title {
        font-size: clamp(1.5rem, 3vw, 2rem);
        font-weight: 700;
        color: #0F172A;
        text-align: center;
        letter-spacing: -0.02em;
        margin: 1.25rem 0 0.5rem 0;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #0F172A;
        text-align: center;
        margin: 1.25rem 0 0.75rem 0;
        letter-spacing: -0.01em;
    }

    /* === Modern step indicator === */
    .step-progress {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        margin: 1.25rem 0 2rem 0;
        flex-wrap: wrap;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.3rem 0.6rem;
    }
    .step-circle {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.85rem;
        border: 2px solid;
        flex-shrink: 0;
        transition: all 0.2s;
    }
    .step-item.done .step-circle {
        background: #3B82F6;
        color: #FFFFFF;
        border-color: #3B82F6;
    }
    .step-item.active .step-circle {
        background: #FFFFFF;
        color: #2563EB;
        border-color: #2563EB;
        box-shadow: 0 0 0 4px rgba(59,130,246,0.12);
    }
    .step-item.upcoming .step-circle {
        background: #FFFFFF;
        color: #94A3B8;
        border-color: rgba(15,23,42,0.15);
    }
    .step-label {
        font-size: 0.9rem;
        font-weight: 500;
    }
    .step-item.done .step-label { color: #3B82F6; }
    .step-item.active .step-label { color: #0F172A; font-weight: 600; }
    .step-item.upcoming .step-label { color: #94A3B8; }
    .step-connector {
        width: 56px;
        height: 2px;
        background: rgba(15,23,42,0.1);
        margin: 0 0.25rem;
    }
    .step-connector.done {
        background: #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# Horizontal navigation menu
col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    if st.button("Home", use_container_width=True):
        st.switch_page("Home.py")
with col_nav2:
    if st.button("AI 3D Generation", use_container_width=True):
        st.switch_page("pages/1_AI_3D_Generation.py")
with col_nav3:
    if st.button("Print With Us", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Print_With_Us.py")

st.divider()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import the API handler
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    API_AVAILABLE = True
except:
    API_AVAILABLE = False

# Try to import the RAG engine
try:
    from rag_engine import query_materials, get_index_stats, force_rebuild
    RAG_AVAILABLE = True
except Exception:
    RAG_AVAILABLE = False

def safe_mesh_volume_mm3(mesh):
    """Return a usable mm³ volume even for non-watertight meshes.
    trimesh.Trimesh.volume returns 0 (or a nonsense value) when the mesh
    isn't a closed manifold — common for STLs exported from some CAD
    tools. Fall back to the axis-aligned bounding-box volume in that case
    so weight/cost don't collapse to zero."""
    try:
        v = float(mesh.volume)
    except Exception:
        v = 0.0
    try:
        e = mesh.extents
        bbox_v = float(e[0]) * float(e[1]) * float(e[2])
    except Exception:
        bbox_v = 0.0
    if v <= 0 or (bbox_v > 0 and v < 0.01 * bbox_v):
        return bbox_v
    return v


# ============== BAMBU STUDIO CLI HELPERS ==============

def check_bambu_cli():
    """Check if Bambu Studio CLI is available in system PATH"""
    try:
        # Try common CLI names
        cli_names = ['bambu-cli', 'BambuStudio-cli', 'bambu_studio_cli']
        
        for cli_name in cli_names:
            result = subprocess.run(
                [cli_name, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False

def build_bambu_cli_command(input_path, output_path, recommendations, custom_cli_path=None):
    """Build Bambu Studio CLI command from recommendations"""
    
    # Determine CLI executable
    cli_exe = custom_cli_path if custom_cli_path else 'bambu-cli'
    
    # Base command - adjust based on actual CLI syntax
    cmd = [
        cli_exe,
        'slice',
        input_path,
        '-o', output_path,
    ]
    
    # Add material parameter
    material = recommendations.get('material', 'PLA').split()[0].upper()
    cmd.extend(['--filament-type', material])
    
    # Add layer height
    layer_height = recommendations.get('layer_height', '0.2')
    cmd.extend(['--layer-height', str(layer_height)])
    
    # Add infill
    infill = recommendations.get('infill', '20')
    cmd.extend(['--infill-density', f"{infill}%"])
    
    # Add wall count
    walls = recommendations.get('walls', '3')
    cmd.extend(['--wall-loops', str(walls)])
    
    # Add support setting
    supports = recommendations.get('supports', 'Auto')
    if supports.lower() != 'none':
        cmd.append('--support-material')
    
    return cmd

def build_bambu_config_json(recommendations, input_path, output_path):
    """Build a JSON configuration file for Bambu Studio CLI"""
    
    config = {
        "input": input_path,
        "output": output_path,
        "print_settings": {
            "layer_height": float(recommendations.get('layer_height', '0.2')),
            "infill_density": int(recommendations.get('infill', '20')),
            "perimeters": int(recommendations.get('walls', '3')),
            "support_material": recommendations.get('supports', 'Auto').lower() != 'none',
        },
        "filament_settings": {
            "filament_type": recommendations.get('material', 'PLA').split()[0].upper(),
        }
    }
    
    return config

# ============================================

st.title("Professional 3D Printing Service")
st.write("Upload your STL file and let AI recommend optimal materials and print settings")

# Initialize session state
if "print_workflow_step" not in st.session_state:
    st.session_state.print_workflow_step = 1  # 1=Upload, 2=Analysis, 3=Confirmation

# Progress indicator (modern step pills)
steps = ["Upload Model", "AI Analysis", "Order Confirmation"]
current_step = st.session_state.print_workflow_step
step_html = '<div class="step-progress">'
for i, step_name in enumerate(steps, 1):
    if i < current_step:
        cls, icon = "done", "✓"
    elif i == current_step:
        cls, icon = "active", str(i)
    else:
        cls, icon = "upcoming", str(i)
    step_html += (
        f'<div class="step-item {cls}">'
        f'<div class="step-circle">{icon}</div>'
        f'<span class="step-label">{step_name}</span>'
        f'</div>'
    )
    if i < len(steps):
        connector_cls = "done" if i < current_step else ""
        step_html += f'<div class="step-connector {connector_cls}"></div>'
step_html += '</div>'
st.markdown(step_html, unsafe_allow_html=True)

st.divider()

# ============== STEP 1: UPLOAD MODEL ==============
if st.session_state.print_workflow_step == 1:
    st.markdown("<h1 class='page-title'>Step 1: Upload Your 3D Model</h1>", unsafe_allow_html=True)
    
    # Check if STL was transferred from generation service
    if "print_service_stl" in st.session_state and st.session_state.print_service_stl:
        st.success("STL file loaded from 3D Generation service!")
        st.session_state.uploaded_stl_data = st.session_state.print_service_stl
        st.session_state.uploaded_stl_name = "generated_model.stl"
        # Clear the transfer variable
        del st.session_state.print_service_stl
    
    # STL Upload
    uploaded_stl = st.file_uploader(
        "Upload STL File",
        type=['stl'],
        help="Upload your 3D model file in STL format"
    )
    
    if uploaded_stl:
        st.session_state.uploaded_stl_data = uploaded_stl.read()
        st.session_state.uploaded_stl_name = uploaded_stl.name
        uploaded_stl.seek(0)
        
        # Show file info
        file_size_kb = len(st.session_state.uploaded_stl_data) / 1024
        st.info(f"File: {uploaded_stl.name} ({file_size_kb:.2f} KB)")
        
        # Try to analyze STL and show 3D preview
        try:
            import trimesh
            import numpy as np
            import plotly.graph_objects as go

            # Load STL from bytes
            mesh = trimesh.load(trimesh.util.wrap_as_stream(st.session_state.uploaded_stl_data), file_type='stl')

            # Store mesh for later use
            st.session_state.print_mesh = mesh

            # ── 3D Preview ────────────────────────────────────────────
            verts = mesh.vertices
            faces = mesh.faces

            if len(verts) > 0 and len(faces) > 0:
                # Build wireframe edge lines
                edge_set = set()
                for f in faces:
                    for a, b in [(f[0], f[1]), (f[1], f[2]), (f[2], f[0])]:
                        edge_set.add((min(a, b), max(a, b)))
                xe, ye, ze = [], [], []
                for a, b in edge_set:
                    xe += [verts[a][0], verts[b][0], None]
                    ye += [verts[a][1], verts[b][1], None]
                    ze += [verts[a][2], verts[b][2], None]

                fig = go.Figure()
                fig.add_trace(go.Mesh3d(
                    x=verts[:, 0].tolist(),
                    y=verts[:, 1].tolist(),
                    z=verts[:, 2].tolist(),
                    i=faces[:, 0].tolist(),
                    j=faces[:, 1].tolist(),
                    k=faces[:, 2].tolist(),
                    color='#b0d4f1',
                    opacity=1.0,
                    flatshading=True,
                    lighting=dict(ambient=0.5, diffuse=0.7, specular=0.3, roughness=0.4),
                    lightposition=dict(x=100, y=200, z=300),
                    hoverinfo='skip',
                ))
                fig.add_trace(go.Scatter3d(
                    x=xe, y=ye, z=ze,
                    mode='lines',
                    line=dict(color='#1a1a2e', width=1.5),
                    hoverinfo='skip',
                    showlegend=False,
                ))
                fig.update_layout(
                    scene=dict(
                        bgcolor='#0F172A',
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
                        zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
                        aspectmode='data',
                    ),
                    paper_bgcolor='#0F172A',
                    plot_bgcolor='#0F172A',
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=380,
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                # Mesh stats below preview
                c1, c2, c3 = st.columns(3)
                c1.metric("Vertices", f"{len(verts):,}")
                c2.metric("Faces", f"{len(faces):,}")
                c3.metric("Volume", f"{safe_mesh_volume_mm3(mesh) / 1000:.2f} cm³")

        except Exception as e:
            st.warning(f"Could not analyze STL file: {str(e)}")

    st.divider()
    
    # Use Case Description (Mandatory)
    st.markdown("<h3 class='section-title'>Describe Your Use Case</h3>", unsafe_allow_html=True)
    st.write("This information helps our AI recommend the best material and print settings.")
    
    use_case_description = st.text_area(
        "**Use Case Description*** (Required)",
        placeholder="""Example: This is a mounting bracket for outdoor use. It will be exposed to:
- Weather: Rain, UV radiation, temperature range -10°C to 40°C
- Mechanical forces: Will hold up to 5kg weight
- Installation: Bolted to a metal frame
- Desired properties: Weather resistant, strong, rigid""",
        height=150,
        help="Describe how the part will be used, environmental factors, and forces it will experience"
    )
    
    st.session_state.use_case_description = use_case_description
    
    st.divider()
    
    # Optional: Preferred Material
    st.markdown("<h3 class='section-title'>Material Preference (Optional)</h3>", unsafe_allow_html=True)
    
    material_options = [
        "Let AI Decide (Recommended)",
        "PLA - General purpose, biodegradable, low heat resistance (Tg ~60°C)",
        "PETG - Outdoor use, moderate heat resistance (Tg ~69°C), weather resistant",
        "TPU 95A - Flexible, rubber-like, impact resistant, gaskets and seals",
    ]
    
    preferred_material = st.selectbox(
        "Preferred Material",
        material_options,
        help="Select a specific material or let AI choose based on your use case"
    )
    
    st.session_state.preferred_material = preferred_material
    
    # Additional preferences
    col1, col2 = st.columns(2)
    color_preference = st.text_input("Color Preference (Optional)", placeholder="e.g., Black, White, Red")
    st.session_state.color_preference = color_preference
    
    st.divider()
    
    # Proceed button
    if st.button("Analyze & Get Recommendations", type="primary", use_container_width=True):
        if not use_case_description:
            st.error("Please provide a use case description")
        elif "uploaded_stl_data" not in st.session_state:
            st.error("Please upload an STL file")
        else:
            st.session_state.print_workflow_step = 2
            st.rerun()

# ============== STEP 2: AI ANALYSIS ==============
elif st.session_state.print_workflow_step == 2:
    st.markdown("<h1 class='page-title'>Step 2: AI Analysis & Recommendations</h1>", unsafe_allow_html=True)
    
    with st.spinner("Analyzing your requirements..."):
        # Simulate AI analysis
        time.sleep(2)
        
        # Get use case description
        use_case = st.session_state.use_case_description
        preferred_mat = st.session_state.preferred_material

        # ── RAG: retrieve relevant material context ──────────────────────────
        rag_context = ""
        rag_active = False
        if RAG_AVAILABLE:
            try:
                rag_context = query_materials(use_case)
                rag_active = bool(rag_context.strip())
            except Exception as _rag_err:
                print(f"[RAG] context retrieval failed: {_rag_err}")

        # Build the context block injected into the prompt
        if rag_context:
            context_block = (
                "\n\nMATERIAL DATABASE CONTEXT\n"
                "(Retrieved from your curated material datasheets — "
                "use this as your PRIMARY reference for material selection and settings):\n"
                f"{rag_context}\n"
            )
        else:
            context_block = ""
        # ─────────────────────────────────────────────────────────────────────

        # AI Analysis using GPT
        if API_AVAILABLE:
            try:
                prompt = f"""You are an expert 3D printing consultant. Analyze this use case and provide material and print parameter recommendations.{context_block}
Use Case Description:
{use_case}

User's Preferred Material: {preferred_mat}

MATERIAL SELECTION RULES (strictly follow — validated against the A1 Mini material database):
- PLA: Indoor use only. Low heat resistance (Tg ~60°C) — do NOT recommend for outdoor, high-temperature, or load-bearing applications. Degrades under prolonged UV exposure. Best for prototypes, decorative, and low-stress indoor parts.
- PETG: The DEFAULT choice for outdoor, functional, and moderate-temperature applications. UV-resistant, water-resistant, tougher than PLA. Use whenever the use case involves outdoor exposure, humidity, moderate heat, or mechanical stress.
- TPU 95A: Flexible parts only. Use when flexibility, impact absorption, or rubber-like properties are needed.
- If the use case mentions outdoor, UV, sun, weather, humidity, garden, or exterior — you MUST recommend PETG, not PLA.
- If the MATERIAL DATABASE CONTEXT above specifies a material for this use case, that overrides everything else.
- If the user has specified a preferred material that is unsuitable, recommend the correct one and clearly explain why.

INFILL RULES (strictly follow — pick ONE exact value from the list below, no ranges):
- Decorative / display / non-functional: 15%
- General-purpose functional parts (everyday use, enclosures, brackets): 25%
- Mechanically loaded parts (clips, hinges, mounts under moderate stress): 40%
- High-stress structural parts (load-bearing, impact-critical): 60%
- Extreme mechanical load (last resort only, must justify): 80%
NEVER output 100%. Choose the single value that best matches the use case and output only that integer.
If the MATERIAL DATABASE CONTEXT above specifies an infill value, use that instead.

Provide a detailed recommendation including:
1. Recommended material (and why)
2. Layer height (mm)
3. Infill percentage (follow the INFILL RULES above)
4. Wall thickness (number of perimeters)
5. Support structure requirements
6. Post-processing recommendations
7. Estimated print time range
8. Any special considerations
9. Limitations — what this material/setup CANNOT handle or is NOT suitable for (e.g. high heat, load-bearing, chemical exposure, outdoor UV, food contact, etc.). Be specific and practical. List 2–4 clear limitations the user must be aware of before ordering.

Format as JSON with these keys: material, layer_height, infill, walls, supports, post_processing, print_time, considerations, reasoning, limitations
The value for "infill" must be a number (no % sign), e.g. "40".
The value for "limitations" must be a plain string (not a list), e.g. "Not suitable for temperatures above 60 degrees C. Avoid prolonged UV exposure. Do not use for load-bearing structural applications."
"""

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert 3D printing consultant specializing in material science and FDM printing parameters. When material database context is provided, base your recommendations primarily on that curated data rather than general knowledge. Never recommend 100% infill — it wastes material and adds weight without proportional strength benefit."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0
                )
                
                ai_response = response.choices[0].message.content
                
                # Try to parse JSON or use text
                import json
                try:
                    # Try to extract JSON from response
                    json_start = ai_response.find('{')
                    json_end = ai_response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        recommendations = json.loads(ai_response[json_start:json_end])
                    else:
                        # Fallback to default
                        raise ValueError("No JSON found")
                except:
                    # Fallback recommendations
                    recommendations = {
                        "material": "ASA",
                        "layer_height": "0.2",
                        "infill": "20",
                        "walls": "4",
                        "supports": "Tree supports",
                        "post_processing": "Remove supports, light sanding",
                        "print_time": "8-12 hours",
                        "considerations": "Based on outdoor use and weather resistance requirements",
                        "reasoning": ai_response
                    }
                
            except Exception as e:
                st.warning(f"AI analysis unavailable: {str(e)}")
                # Default recommendations
                recommendations = {
                    "material": "PETG",
                    "layer_height": "0.2",
                    "infill": "20",
                    "walls": "3",
                    "supports": "Auto-generated",
                    "post_processing": "Remove supports",
                    "print_time": "6-10 hours",
                    "considerations": "General purpose settings",
                    "reasoning": "Default recommendation for functional parts"
                }
        else:
            # Demo mode recommendations
            recommendations = {
                "material": "ASA",
                "layer_height": "0.2",
                "infill": "20",
                "walls": "4",
                "supports": "Tree supports",
                "post_processing": "Remove supports, UV resistant coating",
                "print_time": "8-12 hours",
                "considerations": "Weather resistant for outdoor use",
                "reasoning": "ASA selected for UV resistance and outdoor durability based on your use case"
            }
        
        st.session_state.recommendations = recommendations
    
    # Display recommendations
    st.success("Analysis Complete!")

    # ── RAG status badge ────────────────────────────────────────────────────
    if RAG_AVAILABLE and rag_active:
        stats = get_index_stats()
        st.info(
            f"🔬 **RAG active** — recommendations grounded in your material database "
            f"({stats['num_pdfs']} PDF(s), {stats['num_chunks']} chunks)"
        )
    elif RAG_AVAILABLE and not rag_active:
        stats = get_index_stats()
        col_rag1, col_rag2 = st.columns([3, 1])
        with col_rag1:
            if stats['num_chunks'] == 0:
                st.warning("⚠️ Material database is empty. Drop PDFs into the `rag_docs/` folder to enable RAG-grounded recommendations.")
            else:
                st.warning(
                    f"⚠️ Material database has {stats['num_pdfs']} PDF(s) "
                    f"({stats['num_chunks']} chunks) but couldn't match your "
                    f"use-case description. Try a more specific description "
                    f"for stronger database-grounded recommendations."
                )
        with col_rag2:
            if st.button("Rebuild Index", use_container_width=True):
                with st.spinner("Rebuilding RAG index…"):
                    force_rebuild()
                st.rerun()
    # ────────────────────────────────────────────────────────────────────────

    st.markdown("<h3 class='section-title'>AI-Recommended Print Settings</h3>", unsafe_allow_html=True)

    # Material
    st.markdown(f"### Recommended Material: **{recommendations['material']}**")
    if 'reasoning' in recommendations:
        st.info(recommendations['reasoning'])

    if 'limitations' in recommendations and recommendations['limitations']:
        st.warning(f"⚠️ **Limitations & Constraints**\n\n{recommendations['limitations']}")

    st.divider()
    st.caption("You can adjust the AI's recommendations below before confirming your order.")

    # Editable print parameters
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h3 class='section-title' style='text-align:left; margin-top:0;'>Print Parameters</h3>", unsafe_allow_html=True)

        material_options = ["PLA", "PETG", "TPU 95A"]
        ai_mat = recommendations['material']
        mat_index = next((i for i, m in enumerate(material_options) if ai_mat.upper().startswith(m.split()[0].upper())), 0)
        selected_material = st.selectbox("Material", material_options, index=mat_index, key="edit_material")
        recommendations['material'] = selected_material

        # Bambu A1 Mini standard layer heights (matches Bambu Studio profiles)
        A1_MINI_LAYER_HEIGHTS = [0.08, 0.12, 0.16, 0.20, 0.24, 0.28]
        try:
            lh_val = float(recommendations['layer_height'])
        except (ValueError, TypeError):
            lh_val = 0.20
        selected_layer_height = st.select_slider(
            "Layer Height (mm)",
            options=A1_MINI_LAYER_HEIGHTS,
            value=min(A1_MINI_LAYER_HEIGHTS, key=lambda x: abs(x - lh_val)),
            key="edit_layer_height",
            help="Bambu Lab A1 Mini standard layer heights. Lower = finer detail but slower.",
        )
        recommendations['layer_height'] = f"{selected_layer_height:.2f}"

        try:
            infill_val = int(str(recommendations['infill']).replace('%', '').strip())
        except (ValueError, TypeError):
            infill_val = 25
        selected_infill = st.slider(
            "Infill (%)",
            min_value=5, max_value=80,
            value=min(max(infill_val, 5), 80),
            step=5,
            key="edit_infill",
            help="Higher infill = stronger part but more material and time.",
        )
        recommendations['infill'] = str(selected_infill)

        try:
            walls_val = int(str(recommendations['walls']).split()[0])
        except (ValueError, TypeError):
            walls_val = 3
        selected_walls = st.number_input(
            "Wall Perimeters",
            min_value=1, max_value=8,
            value=min(max(walls_val, 1), 8),
            step=1,
            key="edit_walls",
            help="Number of solid wall loops around the perimeter.",
        )
        recommendations['walls'] = str(selected_walls)

    with col2:
        st.markdown("<h3 class='section-title' style='text-align:left; margin-top:0;'>Post-Processing</h3>", unsafe_allow_html=True)

        st.write("**Supports:** Auto-generated by the slicer based on geometry")

        selected_post = st.text_area(
            "Post-Processing Steps",
            value=str(recommendations.get('post_processing', '')),
            height=110,
            key="edit_post",
        )
        recommendations['post_processing'] = selected_post

        if 'considerations' in recommendations:
            st.markdown(f"**Notes:** {recommendations['considerations']}")
    
    st.divider()
    
    # Bambu Studio Configuration
    st.markdown("<h3 class='section-title'>Bambu Studio Configuration</h3>", unsafe_allow_html=True)
    st.info("These parameters will be used to configure Bambu Studio CLI for automatic slicing")
    
    # Generate bambu studio command preview
    bambu_config = f"""# Bambu Studio CLI Configuration
Material: {recommendations['material']}
Layer Height: {recommendations['layer_height']}mm
Infill: {recommendations['infill']}%
Walls: {recommendations['walls']}
Support: {recommendations['supports']}

# Command preview:
bambu-cli --material {recommendations['material'].lower()} \\
          --layer-height {recommendations['layer_height']} \\
          --infill {recommendations['infill']} \\
          --perimeters {recommendations['walls']} \\
          --support auto \\
          --output sliced_model.3mf \\
          {st.session_state.uploaded_stl_name}
"""
    
    with st.expander("View Bambu Studio CLI Configuration"):
        st.code(bambu_config, language="bash")
    
    st.session_state.bambu_config = bambu_config
    
    # Cost estimate
    st.divider()
    st.markdown("<h3 class='section-title'>Estimated Cost</h3>", unsafe_allow_html=True)

    # ── Activity-Based Costing (ABC) ─────────────────────────────────────────
    # Formula: P_total = [(W_total * C_mat) + (T_print * C_machine) + C_labor] * (1+M) + C_logistics
    # All rates derived from Bambu Lab A1 Mini operating in Belgium (residential electricity)

    # Machine hourly rate breakdown (€/hour):
    #   Depreciation : €200 printer / 2000h warranty cycle  = €0.100
    #   Electricity  : 0.08 kW × €0.382/kWh (Belgian res.) = €0.031
    #   Consumables  : nozzle, build plate, wiper, cutter   = €0.056
    #   Maint. labor : lube/clean + major overhaul amort.   = €0.083
    #   TOTAL                                               = €0.270
    C_MACHINE_PER_HOUR = 0.27   # €/hour

    # Material: retail pricing from Bambu Lab EU store (€/kg) + density (g/cm³)
    MATERIAL_DATA = {
        "PLA":  {"cost_per_kg": 22.99, "density": 1.24},
        "PETG": {"cost_per_kg": 22.99, "density": 1.27},
        "TPU":  {"cost_per_kg": 27.99, "density": 1.21},
    }

    C_LABOR   = 5.00   # €/order — flat post-processing & packing fee
    C_PACKAGING = 1.23 # €/order — box + bubble wrap + label + tape
    C_SHIPPING  = 5.15 # €/order — bpost home delivery (standard, Belgium)
    C_LOGISTICS = C_PACKAGING + C_SHIPPING

    # Margin: 50% total (15% failure tax + 15% growth fund + 20% profit/promotions)
    MARGIN = 0.50

    if "print_mesh" in st.session_state:
        mesh = st.session_state.print_mesh
        bbox_volume_cm3 = max(safe_mesh_volume_mm3(mesh) / 1000, 0.001)  # mm³ → cm³, with bbox fallback for non-watertight meshes

        # Identify selected material
        base_material = recommendations['material'].split()[0].upper()
        mat_data = MATERIAL_DATA.get(base_material, MATERIAL_DATA["PLA"])

        # ── Bambu A1 Mini-accurate weight calculation ───────────────────────────
        # A printed part is NOT a solid block — it has a shell (walls + top/bottom
        # solid layers) and an infill lattice inside. Treating the whole bbox volume
        # as solid (the old code) over-estimates weight by 2–4×.
        #
        # Effective density factor = shell_fraction + (1 − shell_fraction) × infill
        #   • shell_fraction grows with wall count (more perimeters = more solid)
        #     Empirically for a 0.4 mm nozzle on the A1 Mini:
        #       2 walls ≈ 0.22   3 walls ≈ 0.27   4 walls ≈ 0.32
        #     (clamped to 0.55 to handle very small/thin parts where shell dominates)
        #   • infill is the radio-selected percentage (10 / 15 / 25 / etc.)
        #
        # Support overhead: brim + small tree supports add ~10–15% on average.
        infill_pct = int(recommendations['infill']) / 100.0
        n_walls = int(recommendations['walls'])
        shell_fraction = min(0.15 + 0.04 * n_walls, 0.55)
        effective_density_factor = shell_fraction + (1 - shell_fraction) * infill_pct
        SUPPORT_OVERHEAD = 1.12

        weight_g = bbox_volume_cm3 * mat_data["density"] * effective_density_factor * SUPPORT_OVERHEAD
        c_material = (weight_g / 1000) * mat_data["cost_per_kg"]

        # ── Bambu A1 Mini-accurate print time ───────────────────────────────────
        # Effective volumetric flow on the A1 Mini, measured across real prints
        # (0.4 mm nozzle, default Bambu Studio profiles, PLA/PETG). These figures
        # already bake in travel moves, retractions, infill patterns and
        # acceleration — so applying them to actual filament volume gives a
        # realistic wall-clock estimate.
        FLOW_MM3_S_BY_LAYER = {
            "0.28": 6.0,   # Draft
            "0.24": 5.3,   # Speed
            "0.20": 4.5,   # Standard
            "0.16": 3.5,   # Optimal
            "0.12": 2.5,   # Fine
            "0.08": 1.5,   # Extra fine
        }
        layer_h_str = str(recommendations['layer_height'])
        effective_flow = FLOW_MM3_S_BY_LAYER.get(layer_h_str, 4.5)

        # Actual filament volume (mm³) — what the extruder really pushes through
        material_volume_mm3 = bbox_volume_cm3 * 1000 * effective_density_factor * SUPPORT_OVERHEAD
        t_print_hours = max(material_volume_mm3 / (effective_flow * 3600), 0.25)

        c_machine = t_print_hours * C_MACHINE_PER_HOUR

        # ABC total before margin
        c_part = c_material + c_machine + C_LABOR

        # Apply margin + logistics
        total_cost = c_part * (1 + MARGIN) + C_LOGISTICS

        st.session_state.total_cost = total_cost
        recommendations['print_time'] = f"~{t_print_hours:.1f} hours"

        # Display breakdown
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Material", f"€{c_material:.2f}",
                      help=f"{weight_g:.1f} g × €{mat_data['cost_per_kg']}/kg | "
                           f"shell {shell_fraction:.0%} + infill {infill_pct:.0%} of bbox × {SUPPORT_OVERHEAD:.0%} support")
        with col2:
            st.metric("Machine", f"€{c_machine:.2f}",
                      help=f"~{t_print_hours:.1f} h × €{C_MACHINE_PER_HOUR}/h | "
                           f"A1 Mini flow {effective_flow} mm³/s @ {layer_h_str} mm layer")
        with col3:
            st.metric("Labor + Logistics", f"€{C_LABOR + C_LOGISTICS:.2f}",
                      help=f"€{C_LABOR} handling + €{C_PACKAGING} packaging + €{C_SHIPPING} shipping (bpost home)")
        with col4:
            st.metric("**Total (50% margin)**", f"€{total_cost:.2f}",
                      help="Includes 15% failure buffer, 15% growth fund, 20% profit margin")

        with st.expander("View cost breakdown"):
            st.markdown(f"""
| Component | Value | Rate | Cost |
|---|---|---|---|
| Bounding volume | {bbox_volume_cm3:.1f} cm³ | — | — |
| Effective density factor | {effective_density_factor:.3f} | shell {shell_fraction:.0%} + ({1-shell_fraction:.0%} × {infill_pct:.0%} infill) | — |
| Filament weight ({base_material}) | {weight_g:.1f} g | €{mat_data['cost_per_kg']}/kg | €{c_material:.2f} |
| Print time (A1 Mini) | ~{t_print_hours:.1f} h | {effective_flow} mm³/s @ {layer_h_str} mm | — |
| Machine cost | {t_print_hours:.2f} h | €{C_MACHINE_PER_HOUR}/h | €{c_machine:.2f} |
| Post-processing labor | per order | flat fee | €{C_LABOR:.2f} |
| **Subtotal (pre-margin)** | | | **€{c_part:.2f}** |
| Margin (50%) | failure tax + growth + profit | ×1.50 | €{c_part * MARGIN:.2f} |
| Packaging | per order | flat | €{C_PACKAGING:.2f} |
| Shipping (bpost home) | Belgium | standard | €{C_SHIPPING:.2f} |
| **Total** | | | **€{total_cost:.2f}** |
""")
            st.caption("Estimate is calibrated to the Bambu Lab A1 Mini with default Bambu Studio profiles. Actual cost is finalised after slicing (weight & time read from the generated G-code).")
    else:
        st.info("Upload an STL file in Step 1 to calculate the cost.")
    
    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Back", use_container_width=True, key="back_step2"):
            st.session_state.print_workflow_step = 1
            st.rerun()
    
    with col3:
        if st.button("Confirm Order →", type="primary", use_container_width=True):
            st.session_state.print_workflow_step = 3
            st.rerun()

# ============== STEP 3: ORDER CONFIRMATION ==============
elif st.session_state.print_workflow_step == 3:
    st.markdown("<h1 class='page-title'>Step 3: Order Confirmation</h1>", unsafe_allow_html=True)
    
    st.success("Your print order has been prepared!")
    
    # Order summary
    st.markdown("<h3 class='section-title'>Order Summary</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### File Information")
        st.write(f"**Filename:** {st.session_state.uploaded_stl_name}")
        if "print_mesh" in st.session_state:
            mesh = st.session_state.print_mesh
            st.write(f"**Vertices:** {len(mesh.vertices):,}")
            st.write(f"**Volume:** {safe_mesh_volume_mm3(mesh) / 1000:.2f} cm³")
    
    with col2:
        st.markdown("#### Print Settings")
        rec = st.session_state.recommendations
        st.write(f"**Material:** {rec['material']}")
        st.write(f"**Layer Height:** {rec['layer_height']} mm")
        st.write(f"**Infill:** {rec['infill']}%")
        st.write(f"**Estimated Time:** {rec['print_time']}")
    
    if "total_cost" in st.session_state:
        st.metric("Total Cost (ABC)", f"€{st.session_state.total_cost:.2f}")
    
    st.divider()
    
    # Order placement section
    st.markdown("<h3 class='section-title'>Place Your Order</h3>", unsafe_allow_html=True)
    
    st.info("""
    **What happens next:**
    1. You submit your order with the STL file and AI recommendations
    2. We receive your order and review the specifications
    3. We slice your model using Bambu Studio CLI with the recommended settings
    4. We print your model and ship it to you
    5. Estimated completion: 2-3 business days
    """)
    
    # Show what will be sent to the print operator
    with st.expander("📋 View Order Details (What We'll Receive)"):
        st.markdown("#### Files & Data Sent to Print Operator:")
        st.write(f"**STL File:** {st.session_state.uploaded_stl_name}")
        st.write(f"**File Size:** {len(st.session_state.uploaded_stl_data):,} bytes")
        st.write(f"**Use Case:** {st.session_state.use_case_description}")
        
        st.markdown("#### AI Recommended Settings:")
        rec = st.session_state.recommendations
        st.code(f"""Material: {rec['material']}
Layer Height: {rec['layer_height']}mm
Infill: {rec['infill']}%
Walls: {rec['walls']} perimeters
Supports: {rec['supports']}
Print Time: {rec['print_time']}
Post-Processing: {rec['post_processing']}""")
        
        st.markdown("#### Bambu Studio CLI Command (For Print Operator):")
        bambu_cmd = f"""bambu-cli slice {st.session_state.uploaded_stl_name} -o sliced_model.3mf \\
  --filament-type {rec['material'].split()[0].upper()} \\
  --layer-height {rec['layer_height']} \\
  --infill-density {rec['infill']}% \\
  --wall-loops {rec['walls']} \\
  --support-material"""
        st.code(bambu_cmd, language='bash')
    
    # Place order button
    if st.button("Submit Order for Printing", type="primary", use_container_width=True):
        with st.spinner("Submitting your order..."):
            # Generate order ID
            order_id = str(hash(time.time()))[-6:]
            
            # Create orders directory if it doesn't exist
            orders_dir = Path(__file__).parent.parent / "orders"
            orders_dir.mkdir(exist_ok=True)
            
            # Create order-specific directory
            order_dir = orders_dir / f"order_{order_id}"
            order_dir.mkdir(exist_ok=True)
            
            try:
                # Save STL file
                stl_path = order_dir / st.session_state.uploaded_stl_name
                with open(stl_path, 'wb') as f:
                    f.write(st.session_state.uploaded_stl_data)
                
                # Create order summary text file
                order_summary_content = f"""ORDER SUMMARY
==================
Order ID: #{order_id}
Timestamp: {time.strftime("%Y-%m-%d %H:%M:%S")}

FILE INFORMATION
----------------
STL File: {st.session_state.uploaded_stl_name}
File Size: {len(st.session_state.uploaded_stl_data):,} bytes
Use Case: {st.session_state.use_case_description}

AI RECOMMENDED SETTINGS
------------------------
Material: {rec['material']}
Layer Height: {rec['layer_height']}mm
Infill: {rec['infill']}%
Walls: {rec['walls']} perimeters
Supports: {rec['supports']}
Print Time: {rec['print_time']}
Post-Processing: {rec['post_processing']}

COST ESTIMATE
-------------
Total: ${st.session_state.total_cost:.2f}

BAMBU STUDIO CLI COMMAND
-------------------------
bambu-cli slice {st.session_state.uploaded_stl_name} -o sliced_model.3mf \\
  --filament-type {rec['material'].split()[0].upper()} \\
  --layer-height {rec['layer_height']} \\
  --infill-density {rec['infill']}% \\
  --wall-loops {rec['walls']} \\
  --support-material
"""
                
                summary_path = order_dir / f"order_{order_id}_summary.txt"
                with open(summary_path, 'w') as f:
                    f.write(order_summary_content)
                
                # Save order details as JSON for easier processing
                order_json = {
                    'order_id': order_id,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'stl_file': st.session_state.uploaded_stl_name,
                    'use_case': st.session_state.use_case_description,
                    'recommendations': rec,
                    'total_cost': st.session_state.total_cost,
                    'files': {
                        'stl': str(stl_path),
                        'summary': str(summary_path),
                        'order_dir': str(order_dir)
                    }
                }
                
                json_path = order_dir / f"order_{order_id}_data.json"
                with open(json_path, 'w') as f:
                    json.dump(order_json, f, indent=2)
                
                # Save to session state
                st.session_state.order_id = order_id
                st.session_state.order_placed = True
                st.session_state.order_dir = str(order_dir)
                st.session_state.order_summary_content = order_summary_content
                
                st.success(f"✅ Order files saved to: `{order_dir}`")
                
            except Exception as e:
                st.error(f"❌ Error saving order files: {str(e)}")
                st.exception(e)
    
    if st.session_state.get("order_placed", False):
        st.balloons()
        
        st.divider()
        st.success("🎉 Order Submitted Successfully!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Order ID", f"#{st.session_state.order_id}")
            st.metric("Status", "Pending Review")
        with col2:
            st.metric("Estimated Time", "2-3 business days")
        
        st.divider()
        st.markdown("### What Happens Next:")
        st.markdown("""
        1. **Order Received** ✅
           - Your STL file and AI recommendations have been submitted
        
        2. **Print Operator Reviews**
           - We'll verify the file and settings
           - We'll slice your model using Bambu Studio CLI with the recommended parameters
        
        3. **Slicing & Preparation**
           - Your model will be sliced with these settings:
             - Material: {material}
             - Layer Height: {layer_height}mm
             - Infill: {infill}%
        
        4. **3D Printing**
           - Your model will be printed on our Bambu Lab printer
        
        5. **Quality Check & Shipping**
           - We'll inspect the print and ship it to you
        
        You'll receive email updates at each stage!
        """.format(
            material=st.session_state.recommendations['material'],
            layer_height=st.session_state.recommendations['layer_height'],
            infill=st.session_state.recommendations['infill']
        ))
        
        st.divider()
        
        # Show where files are saved
        if "order_dir" in st.session_state:
            st.info(f"""
            **Order Files Saved:**
            
            All order files have been saved to:
            `{st.session_state.order_dir}`
            
            **Files included:**
            - `{st.session_state.uploaded_stl_name}` - Your STL file
            - `order_{st.session_state.order_id}_summary.txt` - Order summary with CLI command
            - `order_{st.session_state.order_id}_data.json` - Machine-readable order data
            
            **For Print Operator:**
            Use the Print Operator CLI tool to process this order:
            ```
            python print_operator_cli.py --order-file "{st.session_state.order_dir}\\order_{st.session_state.order_id}_summary.txt" --stl-file "{st.session_state.order_dir}\\{st.session_state.uploaded_stl_name}"
            ```
            """)
        
        st.divider()
        
        # Download order summary
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download Order Summary",
                st.session_state.order_summary_content,
                f"order_{st.session_state.order_id}_summary.txt",
                "text/plain",
                use_container_width=True,
                key="download_order_summary"
            )
        with col2:
            st.download_button(
                "Download STL File",
                st.session_state.uploaded_stl_data,
                st.session_state.uploaded_stl_name,
                "application/octet-stream",
                use_container_width=True,
                key="download_stl_copy"
            )
        
        st.divider()
        
        if st.button("Place Another Order", use_container_width=True):
            # Clear session state
            for key in list(st.session_state.keys()):
                if key.startswith("print_") or key in ["order_placed", "order_id", "order_details"]:
                    del st.session_state[key]
            st.session_state.print_workflow_step = 1
            st.rerun()
    
    # Navigation
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Back", use_container_width=True, key="back_step3"):
            st.session_state.print_workflow_step = 2
            st.rerun()
    
    with col3:
        if st.button("Home", use_container_width=True, key="home_step3"):
            st.switch_page("Home.py")

# Footer
st.divider()
st.markdown("""
**Professional Printing Service Features:**
- AI-optimized material selection
- Automatic Bambu Studio CLI slicing
- Professional quality control
- Fast turnaround times
- Operator review before printing
""")

if not API_AVAILABLE:
    st.warning("AI recommendations running in demo mode. Configure OpenAI API for full functionality.")
