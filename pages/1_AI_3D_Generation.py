# AI 3D Generation - CadQuery Engineering Framework
# Conversational phase-based 3D modeling with chat left, preview right

import streamlit as st
import time
import random
import os
import tempfile
import base64
import re
import uuid
from pathlib import Path
import sys

from auth import require_login
from styles import inject_global_styles

# Page config
st.set_page_config(
    page_title="AI 3D Generation",
    layout="wide",
    initial_sidebar_state="collapsed",
)

require_login()
inject_global_styles()

# -- CSS --
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded" rel="stylesheet">
<style>
    /*
     * Shared palette (matches Home.py)
     * --slate-800: #1E293B   surface
     * --slate-400: #94A3B8   muted text
     * --slate-50:  #F8FAFC   primary text
     * --blue-500:  #3B82F6   primary accent
     * --indigo-500:#6366F1   secondary accent (active step)
     */

    *, html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
    }

    /* Force columns and their content to stay top-aligned. Streamlit's
       default flex behavior can vertically center the shorter column's
       content when the other column grows (preview + code editor), which
       makes the layout appear to "jump" between renders. */
    [data-testid="stHorizontalBlock"] {
        align-items: flex-start !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        align-self: flex-start !important;
    }
    [data-testid="stColumn"] > div,
    [data-testid="column"] > div {
        justify-content: flex-start !important;
    }

    /* Hide sidebar and all toggle controls */
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

    /* Chat messages */
    .msg-row {
        display: flex;
        gap: 12px;
        padding: 14px 0;
        animation: fadeIn 0.3s ease;
    }
    .msg-row + .msg-row { border-top: 1px solid rgba(255,255,255,0.06); }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    .msg-avatar {
        width: 32px; height: 32px;
        border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        font-size: 14px; font-weight: 600;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .msg-avatar.user { background: #334155; color: #F8FAFC; }
    .msg-avatar.ai   { background: #3B82F6; color: #fff; }

    .msg-body {
        flex: 1;
        font-size: 0.92rem;
        line-height: 1.65;
    }
    .msg-body p { margin: 0 0 0.5em 0; }
    .msg-body p:last-child { margin-bottom: 0; }

    /* Section label */
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94A3B8;
        margin-bottom: 0.75rem;
    }

    /* Step tracker bar */
    .step-tracker {
        display: flex;
        gap: 0;
        margin-bottom: 16px;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .step-item {
        flex: 1;
        text-align: center;
        padding: 10px 6px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        position: relative;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .step-item .step-num {
        display: block;
        font-size: 0.95rem;
        margin-bottom: 2px;
    }
    .step-item.done {
        background: rgba(59,130,246,0.15);
        color: #3B82F6;
    }
    .step-item.active {
        background: rgba(99,102,241,0.2);
        color: #818CF8;
        box-shadow: inset 0 -3px 0 #6366F1;
    }
    .step-item.upcoming {
        background: rgba(255,255,255,0.03);
        color: #64748B;
        cursor: default;
        opacity: 0.6;
    }
    .step-item.viewing {
        background: rgba(99,102,241,0.12);
        color: #818CF8;
        box-shadow: inset 0 -3px 0 rgba(99,102,241,0.5);
    }

    /* Phase-view back bar */
    .phase-view-bar {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        margin-bottom: 10px;
        border-radius: 6px;
        background: rgba(99,102,241,0.08);
        border: 1px solid rgba(99,102,241,0.2);
        font-size: 0.82rem;
    }
    .phase-view-bar .back-label {
        color: #94A3B8;
        font-size: 0.78rem;
    }

    /* Next-step guidance banner */
    .next-step-banner {
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
        font-size: 0.85rem;
        line-height: 1.5;
        display: flex;
        align-items: flex-start;
        gap: 10px;
    }
    .next-step-banner .banner-icon {
        font-size: 1.2rem;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .banner-info  { background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.25); }
    .banner-ready { background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.25); color: #818CF8; }

    /* Preview placeholder */
    .preview-empty {
        border: 1px dashed rgba(255,255,255,0.12);
        border-radius: 12px;
        padding: 2.5rem 2rem;
        text-align: center;
        color: #94A3B8;
    }
    .preview-empty p { margin: 0.5rem 0; }

    /* Subtle divider */
    hr { border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 1rem 0; }

    /* Quick action buttons */
    .quick-actions {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-bottom: 8px;
    }

    /* --- Unified chat input (textarea + action bar share one container look) --- */
    /* Top half: textarea with rounded top corners, attached to bar below */
    textarea[aria-label="Message"] {
        padding: 14px 16px !important;
        background: #1E293B !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-bottom: 1px solid rgba(255,255,255,0.04) !important;
        border-radius: 14px 14px 0 0 !important;
        color: #F8FAFC !important;
        font-size: 0.92rem !important;
        resize: none !important;
        line-height: 1.6 !important;
        transition: border-color 0.15s !important;
        box-shadow: none !important;
    }
    textarea[aria-label="Message"]:focus {
        border-color: rgba(59,130,246,0.45) !important;
        border-bottom-color: rgba(255,255,255,0.04) !important;
        box-shadow: none !important;
        outline: none !important;
    }
    div[data-testid="stTextArea"]:has(textarea[aria-label="Message"]) {
        margin-bottom: 0 !important;
    }

    /* Bottom half: action bar directly attached to textarea — same bg, no gap, rounded bottom */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) {
        background: #1E293B !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-top: none !important;
        border-radius: 0 0 14px 14px !important;
        padding: 8px 14px !important;
        margin-top: 0 !important;
        margin-bottom: 0.75rem !important;
        align-items: center !important;
        gap: 0.5rem !important;
        min-height: 48px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) > div[data-testid="stColumn"] {
        background: transparent !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) > div[data-testid="stColumn"]:last-child {
        justify-content: flex-end !important;
    }

    /* Attach button — strip the file uploader chrome down to just a small button */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) div[data-testid="stFileUploader"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) div[data-testid="stFileUploader"] > div {
        padding: 0 !important;
        margin: 0 !important;
        min-height: 0 !important;
        background: transparent !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) div[data-testid="stFileUploaderDropzone"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        min-height: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) div[data-testid="stFileUploaderDropzoneInstructions"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) div[data-testid="stFileUploader"] small,
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) div[data-testid="stFileUploader"] > label {
        display: none !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) div[data-testid="stFileUploaderDropzone"] button {
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 12px !important;
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 8px !important;
        color: #CBD5E1 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        box-shadow: none !important;
        transform: none !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) div[data-testid="stFileUploaderDropzone"] button:hover {
        background: rgba(255,255,255,0.12) !important;
        color: #F8FAFC !important;
        border-color: rgba(255,255,255,0.18) !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* Send button — themed primary blue, same height as attach */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stFileUploader"]) button[kind="primary"] {
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 16px !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# -- Top navigation --
col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    if st.button("Home", use_container_width=True):
        st.switch_page("Home.py")
with col_nav2:
    if st.button("AI 3D Generation", use_container_width=True, type="primary"):
        st.switch_page("pages/1_AI_3D_Generation.py")
with col_nav3:
    if st.button("Print With Us", use_container_width=True):
        st.switch_page("pages/2_Print_With_Us.py")

st.markdown("<hr>", unsafe_allow_html=True)

# -- Top toolbar: AI Model selector + Dev Mode toggle, stacked on the right --
toolbar_left, toolbar_right = st.columns([5, 1])
with toolbar_right:
    ai_provider = st.selectbox(
        "AI Model",
        options=["OpenAI", "Gemini"],
        index=["OpenAI", "Gemini"].index(st.session_state.get("ai_provider", "OpenAI")),
        key="ai_provider_select",
        label_visibility="collapsed",
    )
    st.session_state.ai_provider = ai_provider
    dev_mode_toggle = st.toggle(
        "Dev Mode",
        value=st.session_state.get("dev_mode", False),
        key="dev_toggle",
    )
    st.session_state.dev_mode = dev_mode_toggle

# -- Imports --
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from api_handler_simple import (
        chat_with_framework,
        extract_cadquery_code,
        detect_phase,
        has_cadquery_code,
    )
    from token_tracker import log_usage, get_summary
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    st.warning("AI API not available. Running in demo mode.")


def format_ai_message(text):
    """Convert markdown-like formatting in AI messages to HTML."""
    import re as _re
    # Strip fenced code blocks — both complete and incomplete (truncated)
    text = _re.sub(r'```[\w]*\s*\n.*?```', '', text, flags=_re.DOTALL)
    text = _re.sub(r'```[\w]*\s*\n.*', '', text, flags=_re.DOTALL)  # unclosed block
    # Bold: **text** or __text__
    text = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = _re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    # Italic: *text* or _text_ (but not inside bold)
    text = _re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # Inline code: `text`
    text = _re.sub(r'`([^`]+)`', r'<code style="background:rgba(128,128,128,0.15);padding:1px 5px;border-radius:3px;font-size:0.85em;">\1</code>', text)
    # Process line by line for lists and paragraphs
    lines = text.split('\n')
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        # Bullet list: lines starting with - or *
        if _re.match(r'^[-*]\s+', stripped):
            if not in_list:
                result.append('<ul style="margin:0.3em 0 0.3em 1.2em;padding:0;">')
                in_list = True
            item = _re.sub(r'^[-*]\s+', '', stripped)
            result.append(f'<li>{item}</li>')
        # Numbered list: lines starting with digit.
        elif _re.match(r'^\d+\.\s+', stripped):
            if not in_list:
                result.append('<ol style="margin:0.3em 0 0.3em 1.2em;padding:0;">')
                in_list = True
            item = _re.sub(r'^\d+\.\s+', '', stripped)
            result.append(f'<li>{item}</li>')
        else:
            if in_list:
                # Close previous list
                result.append('</ul>' if any('<ul' in r for r in result[-20:]) else '</ol>')
                in_list = False
            if stripped:
                result.append(f'{stripped}<br>')
            else:
                result.append('<br>')
    if in_list:
        result.append('</ul>' if any('<ul' in r for r in result[-20:]) else '</ol>')
    return '\n'.join(result)


def execute_cadquery_code(code):
    """Execute CadQuery code and return vertices + faces for visualization."""
    try:
        import cadquery as cq
        from cadquery import exporters, Face, Wire, Workplane
        import numpy as np

        # Strip lines that cause issues in our execution environment
        clean_lines = []
        for line in code.split('\n'):
            stripped = line.strip()
            if stripped.startswith('show_object('):
                continue
            if 'cq.exporters.export(' in stripped or 'exporters.export(' in stripped:
                continue
            if stripped.startswith("if 'show_object'"):
                continue
            clean_lines.append(line)
        code = '\n'.join(clean_lines)

        namespace = {
            'cq': cq,
            'cadquery': cq,
            'Face': Face,
            'Wire': Wire,
            'Workplane': Workplane,
            'np': np,
            '__builtins__': __builtins__,
        }
        exec(code, namespace)

        # Find the result object
        result_obj = None
        for name in ['result', 'solid', 'model', 'part', 'assembly', 'final', 'housing', 'body', 'shape', 'obj',
                     'cube', 'box', 'cylinder', 'sphere', 'plate', 'bracket', 'shell', 'base', 'block',
                     'frame', 'mount', 'flange', 'outer_solid', 'base_body']:
            if name in namespace:
                result_obj = namespace[name]
                break

        # Fallback: find any CadQuery Workplane object in namespace
        if result_obj is None:
            import cadquery as _cq_check
            for name, val in namespace.items():
                if name.startswith('_'):
                    continue
                if isinstance(val, _cq_check.Workplane):
                    result_obj = val
                    break

        if result_obj is None:
            return None, "Code must create a 'result' variable with the final CadQuery object.", None

        # Get the shape for tessellation
        if hasattr(result_obj, 'val'):
            shape = result_obj.val()
        elif hasattr(result_obj, 'toOCC'):
            shape = result_obj.toOCC()
        else:
            shape = result_obj

        import trimesh
        import numpy as np

        # --- OCC tessellation: exact per-face triangle mapping ---
        try:
            from OCP.BRep import BRep_Tool
            from OCP.TopExp import TopExp_Explorer
            from OCP.TopAbs import TopAbs_FACE
            from OCP.BRepMesh import BRepMesh_IncrementalMesh
            from OCP.TopLoc import TopLoc_Location
            from OCP.TopoDS import TopoDS

            occ_shape = shape.wrapped if hasattr(shape, 'wrapped') else shape
            BRepMesh_IncrementalMesh(occ_shape, 0.1, False, 0.1, True)

            all_verts = []
            all_tris = []
            face_ids = []
            vert_offset = 0
            face_idx = 0

            explorer = TopExp_Explorer(occ_shape, TopAbs_FACE)
            while explorer.More():
                face = TopoDS.Face_s(explorer.Current())
                loc = TopLoc_Location()
                poly = BRep_Tool.Triangulation_s(face, loc)
                if poly is not None:
                    trsf = loc.Transformation()
                    n_nodes = poly.NbNodes()
                    n_tris = poly.NbTriangles()
                    for i in range(1, n_nodes + 1):
                        p = poly.Node(i)
                        p.Transform(trsf)
                        all_verts.append([p.X(), p.Y(), p.Z()])
                    for i in range(1, n_tris + 1):
                        tri = poly.Triangle(i)
                        i1, i2, i3 = tri.Get()
                        all_tris.append([i1 - 1 + vert_offset,
                                         i2 - 1 + vert_offset,
                                         i3 - 1 + vert_offset])
                        face_ids.append(face_idx)
                    vert_offset += n_nodes
                face_idx += 1
                explorer.Next()

            if all_verts and all_tris:
                mesh = trimesh.Trimesh(
                    vertices=np.array(all_verts),
                    faces=np.array(all_tris),
                    process=False,
                )
                mesh.metadata['tri_face_map'] = np.array(face_ids)
                return mesh, None, result_obj
        except Exception as occ_err:
            print(f"[DEBUG] OCC tessellation failed, falling back to STL: {occ_err}")

        # --- Fallback: STL export ---
        with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
            tmp_path = tmp.name

        if hasattr(result_obj, 'val'):
            cq.exporters.export(result_obj, tmp_path, cq.exporters.ExportTypes.STL)
        else:
            cq.exporters.export(cq.Workplane().newObject([shape]), tmp_path, cq.exporters.ExportTypes.STL)

        mesh = trimesh.load(tmp_path)
        os.unlink(tmp_path)

        if not isinstance(mesh, trimesh.Trimesh):
            if isinstance(mesh, trimesh.Scene):
                mesh = trimesh.util.concatenate(mesh.dump())
            else:
                return None, f"Unexpected mesh type: {type(mesh)}", None

        return mesh, None, result_obj

    except SyntaxError as e:
        import traceback
        traceback.print_exc()
        # Print the code with line numbers for debugging
        print("\n[DEBUG] Code that failed to parse:")
        for i, ln in enumerate(code.split('\n'), 1):
            marker = " >>>" if i == (e.lineno or -1) else "    "
            print(f"{marker} {i:3d}: {ln}")
        return None, f"CadQuery execution error: {e}", None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"CadQuery execution error: {e}", None


# ---- Measurement helpers ----

def extract_faces_info(cq_result):
    """Extract geometric properties of each face from the CadQuery solid."""
    import numpy as _np
    faces_info = []
    try:
        vals = cq_result.faces().vals()
        for i, face in enumerate(vals):
            geom_type = face.geomType()
            center = face.Center()
            area = face.Area()
            try:
                normal = face.normalAt()
                n = (_np.round(normal.x, 4), _np.round(normal.y, 4), _np.round(normal.z, 4))
            except Exception:
                n = (0, 0, 0)

            # Build a human-readable orientation hint
            cx, cy, cz = round(center.x, 2), round(center.y, 2), round(center.z, 2)
            hint = ""
            if geom_type == "PLANE":
                ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
                if az > 0.9:
                    hint = "Top" if n[2] > 0 else "Bottom"
                elif ax > 0.9:
                    hint = "Right" if n[0] > 0 else "Left"
                elif ay > 0.9:
                    hint = "Front" if n[1] > 0 else "Back"
            label = f"Face {i+1}: {geom_type}"
            if hint:
                label += f" ({hint})"
            label += f" — center=({cx}, {cy}, {cz}), area={area:.1f}"

            faces_info.append({
                'idx': i,
                'type': geom_type,
                'center': (center.x, center.y, center.z),
                'normal': n,
                'area': area,
                'label': label,
            })
    except Exception as e:
        print(f"[DEBUG] extract_faces_info error: {e}")
    return faces_info


def extract_edges_info(cq_result):
    """Extract geometric properties of each edge from the CadQuery solid."""
    edges_info = []
    try:
        vals = cq_result.edges().vals()
        for i, edge in enumerate(vals):
            geom_type = edge.geomType()
            length = edge.Length()
            sp = edge.startPoint()
            ep = edge.endPoint()
            label = (
                f"Edge {i+1}: {geom_type}, L={length:.2f}mm "
                f"({round(sp.x,1)},{round(sp.y,1)},{round(sp.z,1)}) → "
                f"({round(ep.x,1)},{round(ep.y,1)},{round(ep.z,1)})"
            )
            edges_info.append({
                'idx': i,
                'type': geom_type,
                'length': length,
                'start': (sp.x, sp.y, sp.z),
                'end': (ep.x, ep.y, ep.z),
                'label': label,
            })
    except Exception as e:
        print(f"[DEBUG] extract_edges_info error: {e}")
    return edges_info


def compute_face_face(fa, fb):
    """Compute comprehensive relationship between two faces."""
    import numpy as _np
    na = _np.array(fa['normal'])
    nb = _np.array(fb['normal'])
    ca = _np.array(fa['center'])
    cb = _np.array(fb['center'])
    diff = cb - ca

    # Angle between face normals
    dot = _np.clip(_np.dot(na, nb), -1, 1)
    angle_deg = round(_np.degrees(_np.arccos(abs(dot))), 2)

    # Relationship flags
    parallel = abs(abs(dot) - 1.0) < 0.01
    perpendicular = abs(dot) < 0.01

    # Distance
    if parallel:
        distance = round(abs(_np.dot(diff, na)), 4)
    else:
        distance = round(_np.linalg.norm(diff), 4)

    # Coplanar: parallel + zero separation
    coplanar = parallel and distance < 0.01

    # Facing direction for parallel faces
    facing = None
    if parallel:
        facing = "opposing" if dot < 0 else "same direction"

    # Classify the relationship
    if coplanar:
        relation = "Coplanar"
    elif parallel:
        relation = f"Parallel ({facing})"
    elif perpendicular:
        relation = "Perpendicular"
    else:
        relation = f"Angled ({angle_deg}\u00b0)"

    return {
        'distance': distance,
        'angle': angle_deg,
        'parallel': parallel,
        'perpendicular': perpendicular,
        'coplanar': coplanar,
        'facing': facing,
        'relation': relation,
        'center_a': ca.tolist(),
        'center_b': cb.tolist(),
    }


def compute_edge_edge(ea, eb):
    """Compute comprehensive relationship between two edges."""
    import numpy as _np
    sa = _np.array(ea['start'])
    ea_end = _np.array(ea['end'])
    sb = _np.array(eb['start'])
    eb_end = _np.array(eb['end'])

    da = ea_end - sa
    db = eb_end - sb
    la = _np.linalg.norm(da)
    lb = _np.linalg.norm(db)
    if la < 1e-9 or lb < 1e-9:
        return {'angle': None, 'distance': None, 'relation': 'Degenerate',
                'parallel': False, 'perpendicular': False, 'coplanar': False,
                'intersecting': False, 'shared_vertex': None,
                'closest_a': sa.tolist(), 'closest_b': sb.tolist()}

    da_n = da / la
    db_n = db / lb
    dot = _np.clip(abs(_np.dot(da_n, db_n)), 0, 1)
    angle_deg = round(_np.degrees(_np.arccos(dot)), 2)

    parallel = abs(dot - 1.0) < 0.01
    perpendicular = dot < 0.01

    # Closest distance between two line segments
    w0 = sa - sb
    a = float(_np.dot(da, da))
    b = float(_np.dot(da, db))
    c = float(_np.dot(db, db))
    d = float(_np.dot(da, w0))
    e = float(_np.dot(db, w0))
    denom = a * c - b * b

    if abs(denom) < 1e-10:
        sc_p = 0.0
        tc_p = d / b if abs(b) > 1e-10 else 0.0
    else:
        sc_p = (b * e - c * d) / denom
        tc_p = (a * e - b * d) / denom

    sc_p = max(0.0, min(1.0, sc_p))
    tc_p = max(0.0, min(1.0, tc_p))

    closest_a = sa + sc_p * da
    closest_b = sb + tc_p * db
    min_distance = round(float(_np.linalg.norm(closest_a - closest_b)), 4)

    # Coplanar check
    cross = _np.cross(da_n, db_n)
    cross_norm = _np.linalg.norm(cross)
    coplanar = (abs(_np.dot(cross, w0)) < 0.01 * max(la, lb)) if cross_norm > 1e-9 else True

    # Intersecting: coplanar + zero closest distance
    intersecting = coplanar and min_distance < 0.01

    # Shared vertex check
    shared_vertex = None
    for pa in [sa, ea_end]:
        for pb in [sb, eb_end]:
            if _np.linalg.norm(pa - pb) < 0.01:
                shared_vertex = pa.tolist()
                break
        if shared_vertex:
            break

    # Classify
    if shared_vertex:
        relation = "Connected (shared vertex)"
    elif intersecting:
        relation = "Intersecting"
    elif parallel and min_distance < 0.01:
        relation = "Collinear"
    elif parallel:
        relation = "Parallel"
    elif perpendicular and coplanar:
        relation = "Perpendicular (coplanar)"
    elif perpendicular:
        relation = "Perpendicular (skew)"
    elif coplanar:
        relation = f"Coplanar ({angle_deg}\u00b0)"
    else:
        relation = f"Skew ({angle_deg}\u00b0)"

    return {
        'angle': angle_deg,
        'distance': min_distance,
        'parallel': parallel,
        'perpendicular': perpendicular,
        'coplanar': coplanar,
        'intersecting': intersecting,
        'shared_vertex': shared_vertex,
        'relation': relation,
        'closest_a': closest_a.tolist(),
        'closest_b': closest_b.tolist(),
    }


def map_triangles_to_cad_faces(verts, tri_faces, faces_info):
    """Map each mesh triangle to the closest CadQuery face using normals + proximity."""
    import numpy as _np
    n_tris = len(tri_faces)
    n_cad = len(faces_info)
    if n_cad == 0 or n_tris == 0:
        return _np.zeros(n_tris, dtype=int)
    v0 = verts[tri_faces[:, 0]]
    v1 = verts[tri_faces[:, 1]]
    v2 = verts[tri_faces[:, 2]]
    tri_centers = (v0 + v1 + v2) / 3.0
    tri_normals = _np.cross(v1 - v0, v2 - v0)
    norms = _np.linalg.norm(tri_normals, axis=1, keepdims=True)
    norms[norms < 1e-10] = 1.0
    tri_normals /= norms
    cad_centers = _np.array([f['center'] for f in faces_info])
    cad_normals = _np.array([f['normal'] for f in faces_info])
    # Vectorised scoring: normal agreement + center proximity
    normal_dots = _np.abs(tri_normals @ cad_normals.T)       # (N, M)
    diffs = tri_centers[:, None, :] - cad_centers[None, :, :]  # (N, M, 3)
    dists = _np.linalg.norm(diffs, axis=2)                    # (N, M)
    max_dist = max(dists.max(), 1.0)
    scores = normal_dots * 0.4 + (1.0 - dists / max_dist) * 0.6
    return _np.argmax(scores, axis=1)


# -- Session state defaults --
_defaults = {
    "current_code": "",
    "current_phase": 0,
    "phase_name": "",
    "chat_history": [],
    "preview_mesh": None,
    "viewing_phase": None,  # None = view current phase, int = view specific phase
    "dev_mode": False,
    "faces_info": [],
    "edges_info": [],
    "selected_meas_items": [],
    "meas_3d_mode": "View",
    "session_id": str(uuid.uuid4()),
    "generation_id": str(uuid.uuid4()),
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -- Main two-column layout --
col_chat, col_preview = st.columns([1, 1], gap="large", vertical_alignment="top")

# ================================================================
#  LEFT COLUMN - CONVERSATION
# ================================================================
with col_chat:
    st.markdown("<div class='section-label'>Conversation</div>", unsafe_allow_html=True)

    # Step tracker (clickable to view past phases)
    phase = st.session_state.current_phase
    viewing = st.session_state.viewing_phase  # None means viewing current phase
    display_phase = viewing if viewing is not None else phase
    step_names = ["Analyse", "Confirm", "Plan", "Code"]
    steps_html = ""
    for i, name in enumerate(step_names, 1):
        if i < phase:
            cls = "done"
        elif i == phase:
            cls = "active"
        else:
            cls = "upcoming"
        # Highlight the one being viewed
        if viewing is not None and i == viewing and i != phase:
            cls = "viewing"
        steps_html += f"<div class='step-item {cls}'><span class='step-num'>{i}</span>{name}</div>"
    st.markdown(f"<div class='step-tracker'>{steps_html}</div>", unsafe_allow_html=True)

    # Clickable step navigation (one button per step, replaces the step tracker visually)
    if phase > 1:
        step_cols = st.columns(4)
        for i in range(4):
            step_num = i + 1
            with step_cols[i]:
                if step_num <= phase:
                    is_current_view = (viewing is None and step_num == phase) or (viewing == step_num)
                    btn_type = "primary" if is_current_view else "secondary"
                    if st.button(f"{step_num}. {step_names[step_num-1]}", key=f"step_{step_num}",
                                 use_container_width=True, type=btn_type):
                        st.session_state.viewing_phase = step_num if step_num != phase else None
                        st.rerun()

    # If viewing a past phase, show a "back to current" bar
    if viewing is not None and viewing != phase:
        st.markdown(
            f"<div class='phase-view-bar'>"
            f"<span class='back-label'>Viewing Phase {viewing} &mdash; {step_names[viewing - 1]}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        bcol1, bcol2 = st.columns([3, 1])
        with bcol2:
            if st.button("Back to current", key="back_to_current", use_container_width=True):
                st.session_state.viewing_phase = None
                st.rerun()

    # Chat history - filtered by viewed phase
    chat_container = st.container()
    with chat_container:
        history = st.session_state.chat_history

        # Filter messages to only show the phase being viewed
        if history:
            # Tag messages with their phase if not already tagged
            phase_msgs = [m for m in history if m.get("phase", display_phase) == display_phase]

            if not phase_msgs:
                st.markdown(
                    "<div style='color:#666; font-size:0.85rem; padding:1rem 0; text-align:center;'>"
                    f"No messages in Phase {display_phase} yet.</div>",
                    unsafe_allow_html=True,
                )
            else:
                for msg in phase_msgs:
                    avatar_cls = "user" if msg["role"] == "user" else "ai"
                    avatar_letter = "Y" if msg["role"] == "user" else "AI"

                    content_html = msg["content"].replace("\n", "<br>") if msg["role"] == "user" else format_ai_message(msg["content"])

                    st.markdown(
                        f"""<div class='msg-row'>
                            <div class='msg-avatar {avatar_cls}'>{avatar_letter}</div>
                            <div class='msg-body'>{content_html}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    # Show attached images
                    if msg["role"] == "user" and "images" in msg and msg["images"]:
                        img_cols = st.columns(min(len(msg["images"]), 3))
                        for idx, img_bytes in enumerate(msg["images"]):
                            with img_cols[idx % 3]:
                                st.image(img_bytes, width=100)

        else:
            st.markdown(
                "<div style='color:#999; font-size:0.9rem; padding:1rem 0;'>"
                "Describe the 3D part you want to model. You can also attach technical drawings or reference images.<br><br>"
                "The AI will guide you through a structured process:<br>"
                "1. Analyse your request<br>"
                "2. Confirm understanding<br>"
                "3. Generate a build plan<br>"
                "4. Write CadQuery code</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<hr>", unsafe_allow_html=True)

    # -- Next-step guidance banner + action button --
    if phase == 0:
        st.markdown(
            "<div class='next-step-banner banner-info'>"
            "<span class='banner-icon'>1</span>"
            "<div><strong>Step 1 &mdash; Describe your part</strong><br>"
            "Type a description of the 3D model you need, or attach a technical drawing / reference image. "
            "The AI will analyse your request and ask clarification questions if needed.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    elif phase == 1:
        st.markdown(
            "<div class='next-step-banner banner-info'>"
            "<span class='banner-icon'>&#8595;</span>"
            "<div><strong>The AI is waiting for your answer</strong><br>"
            "Read the question above, then type your reply in the text box below. "
            "If you're happy with the AI's understanding, click <em>Confirm Understanding</em>.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    elif phase == 2:
        st.markdown(
            "<div class='next-step-banner banner-ready'>"
            "<span class='banner-icon'>3</span>"
            "<div><strong>Step 3 &mdash; Ready for plan</strong><br>"
            "The AI has confirmed its understanding. Click <em>Generate Plan</em> to create the build strategy, "
            "or type feedback to adjust the understanding first.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    elif phase == 3:
        st.markdown(
            "<div class='next-step-banner banner-ready'>"
            "<span class='banner-icon'>4</span>"
            "<div><strong>Step 4 &mdash; Ready for code</strong><br>"
            "The build plan is ready and checks have passed. Click <em>Generate Code</em> to produce the CadQuery model, "
            "or click <em>Show Plan</em> / <em>Show Checks</em> to review first.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    elif phase == 4:
        st.markdown(
            "<div class='next-step-banner banner-ready'>"
            "<span class='banner-icon'>&#10003;</span>"
            "<div><strong>Model generated</strong><br>"
            "Your 3D model is shown in the preview. You can request changes in the chat, "
            "export the STL, or start a new model.</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    # -- Context-sensitive action button --
    if phase == 1:
        if st.button("Move to Next Phase", type="primary", use_container_width=True, key="qa_advance_1"):
            st.session_state._quick_action = "I confirm this understanding is correct. Please proceed to the next phase."
            st.rerun()
    elif phase == 2:
        if st.button("Move to Next Phase", type="primary", use_container_width=True, key="qa_advance_2"):
            st.session_state._quick_action = "Generate Plan"
            st.rerun()
    elif phase == 3:
        if st.button("Move to Next Phase", type="primary", use_container_width=True, key="qa_advance_3"):
            st.session_state._quick_action = "Generate Code"
            st.rerun()

    # -- Input area --
    phase_placeholders = {
        0: "Describe your 3D part (e.g. 'A mounting bracket with 4 screw holes')...",
        1: "Type your answer here (e.g. 'center of the bottom face is fine')...",
        2: "Provide feedback to adjust the understanding, or click Generate Plan...",
        3: "Provide feedback on the plan, or click Generate Code...",
        4: "Request changes to the model (e.g. 'make the walls thicker')...",
    }
    placeholder_text = phase_placeholders.get(phase, "Type a message...")

    user_input = st.text_area(
        "Message",
        placeholder=placeholder_text,
        height=120,
        label_visibility="collapsed",
        key="chat_input",
    )

    # Action row — CSS pulls this up into the textarea's bottom padding area
    col_attach, col_gap, col_send = st.columns([3, 5, 2])
    with col_attach:
        uploaded_images = st.file_uploader(
            "📎 Attach",
            type=["png", "jpg", "jpeg", "bmp", "gif", "webp"],
            accept_multiple_files=True,
            key="chat_images",
            label_visibility="collapsed",
        )
    with col_send:
        send_clicked = st.button("Send ↑", type="primary", use_container_width=True, key="send_btn")

    if uploaded_images:
        img_row = st.columns(min(len(uploaded_images), 4))
        for idx, img in enumerate(uploaded_images):
            with img_row[idx % 4]:
                st.image(img, width=60)

    # -- Handle quick action if one was pressed --
    quick_action = st.session_state.pop("_quick_action", None)
    message_to_send = quick_action or None

    # -- Process the message --
    # Only send when Send button is clicked or a quick action was triggered
    is_advance_action = False  # Track if this is a phase-advancing action
    if quick_action:
        message_to_send = quick_action
        # These quick actions are explicit phase advancement triggers
        advance_phrases = ["proceed", "confirm", "next phase", "generate plan", "generate code"]
        is_advance_action = any(phrase in quick_action.lower() for phrase in advance_phrases)
    elif send_clicked and (user_input or uploaded_images):
        message_to_send = user_input if user_input else "(image attached)"
    else:
        message_to_send = None

    if message_to_send:
        final_text = message_to_send

        # Collect image bytes
        image_bytes_list = []
        if uploaded_images:
            for img_file in uploaded_images:
                image_bytes_list.append(img_file.read())
                img_file.seek(0)

        # Add user message to history (tagged with current phase)
        chat_msg = {"role": "user", "content": final_text, "phase": max(phase, 1)}
        if image_bytes_list:
            chat_msg["images"] = image_bytes_list
        st.session_state.chat_history.append(chat_msg)

        # Call AI
        token_usage = None
        if API_AVAILABLE:
            with st.spinner("Generating response... this may take a moment"):
                try:
                    ai_response, token_usage = chat_with_framework(
                        st.session_state.chat_history,
                        image_data=image_bytes_list if image_bytes_list else None,
                        provider=st.session_state.get("ai_provider", "OpenAI").lower(),
                        current_phase=max(st.session_state.current_phase, 1),
                    )
                except Exception as e:
                    ai_response = f"Error: {e}"
        else:
                # Demo mode
                time.sleep(1)
                if phase == 0:
                    ai_response = (
                        "PHASE 1 - REQUEST ANALYSIS\n\n"
                        "I have identified your request. Let me analyse the geometry:\n\n"
                        "- Input type: text description\n"
                        "- User intent: 3D part generation\n"
                        "- Geometric structure: to be determined from your description\n\n"
                        "Could you provide the following dimensions?\n"
                        "1. Overall width, height, depth (mm)\n"
                        "2. Any feature dimensions (holes, slots, etc.)\n"
                        "3. Wall thickness if applicable"
                    )
                elif phase == 1 or phase == 2:
                    ai_response = (
                        "PHASE 2 - CONSOLIDATED UNDERSTANDING CONFIRMATION\n\n"
                        "Based on your input, here is my understanding:\n\n"
                        "- Geometry: simple box with features\n"
                        "- Dimensions: as specified\n"
                        "- Origin: center of bottom face\n\n"
                        "Send 'Generate Plan' to proceed, or provide feedback."
                    )
                elif phase == 3:
                    ai_response = (
                        "PHASE 3 - PLAN GENERATION\n\n"
                        "Generation plan ready.\n"
                        "Internal checks passed (delta_end=0, delta_attach=0, residuals=0).\n"
                        "Ready for code generation.\n\n"
                        "Send 'Generate Code' to proceed."
                    )
                else:
                    ai_response = (
                        "PHASE 4 - CODE GENERATION\n\n"
                        "```python\n"
                        "import cadquery as cq\n\n"
                        "# Parameters\n"
                        "width = 50\nheight = 30\ndepth = 20\n\n"
                        "# Step 1: Base box\n"
                        "result = cq.Workplane('XY').box(width, height, depth)\n"
                        "```"
                    )

        # Detect phase from AI response
        detected_phase, detected_name = detect_phase(ai_response) if API_AVAILABLE else (None, None)
        if detected_phase:
            if detected_phase == st.session_state.current_phase:
                # Same phase — always allow (AI staying in current phase)
                st.session_state.phase_name = detected_name
            elif detected_phase > st.session_state.current_phase:
                if is_advance_action or st.session_state.current_phase == 0:
                    # Only advance if user explicitly triggered it (or first message)
                    st.session_state.current_phase = detected_phase
                    st.session_state.phase_name = detected_name
                else:
                    # AI tried to advance but user sent feedback — block it
                    print(f"[DEBUG] Blocked phase advance: AI said Phase {detected_phase} but user sent feedback, staying in Phase {st.session_state.current_phase}")
            # Never allow phase to go backward (implicit: do nothing)
        elif st.session_state.current_phase == 0 and ai_response:
            # First response, set to Phase 1 at minimum
            st.session_state.current_phase = 1

        # Tag AI response with detected phase
        ai_phase = st.session_state.current_phase

        # Log raw AI response to terminal for debugging
        print("\n" + "="*80)
        print(f"[DEBUG] Phase: {ai_phase} | Provider: {st.session_state.get('ai_provider', 'OpenAI')}")
        print(f"[DEBUG] User message: {final_text[:300]}")
        print(f"[DEBUG] AI response ({len(ai_response)} chars):")
        print(ai_response)
        print("="*80 + "\n")

        # Log token usage
        if token_usage and API_AVAILABLE:
            try:
                log_usage(
                    session_id=st.session_state.session_id,
                    generation_id=st.session_state.generation_id,
                    phase=ai_phase,
                    is_feedback=not is_advance_action,
                    provider=st.session_state.get("ai_provider", "OpenAI").lower(),
                    model=token_usage.get("model", "unknown"),
                    prompt_tokens=token_usage.get("prompt_tokens", 0),
                    completion_tokens=token_usage.get("completion_tokens", 0),
                    total_tokens=token_usage.get("total_tokens", 0),
                    thinking_tokens=token_usage.get("thinking_tokens", 0),
                    user_message_preview=final_text,
                )
            except Exception as e:
                print(f"[DEBUG] Token logging error: {e}")

        # Start a new generation cycle when Phase 4 code is produced
        if ai_phase == 4 and is_advance_action:
            st.session_state.generation_id = str(uuid.uuid4())

        # Reset viewing to current phase after sending a message
        st.session_state.viewing_phase = None

        # Auto-detect and execute CadQuery code if present (Phase 4 only)
        if ai_phase == 4 and (has_cadquery_code(ai_response) if API_AVAILABLE else ('```python' in ai_response)):
            code = extract_cadquery_code(ai_response) if API_AVAILABLE else None
            if code is None and '```python' in ai_response:
                # Manual extraction for demo mode
                match = re.search(r'```python\s*\n(.*?)```', ai_response, re.DOTALL)
                if match:
                    code = match.group(1).strip()

            if code:
                # Auto-inject result= if the code doesn't have it
                if 'result' not in code and 'result =' not in code:
                    import re as _re
                    # Skip variables that are clearly not geometry
                    _skip_vars = {'bb', 'bbox', 'bounding_box', 'np', 'cq', 'cadquery',
                                  'math', 'os', 'exporters', 'i', 'j', 'k', 'x', 'y', 'z',
                                  'tmp', 'temp', 'f', 'line', 'lines', 'idx', 'val', 'name'}
                    # Known geometry variable names
                    _geo_names = ['cube', 'box', 'cylinder', 'sphere', 'plate', 'bracket',
                                  'outer_solid', 'base_body', 'housing', 'body', 'solid',
                                  'part', 'model', 'shape', 'obj', 'assembly', 'final',
                                  'shell', 'base', 'block', 'frame', 'mount', 'flange']
                    # First try: find assignments to known geometry names
                    last_geo = _re.findall(
                        r'^(' + '|'.join(_geo_names) + r')\s*=',
                        code, _re.MULTILINE,
                    )
                    if last_geo:
                        code += f"\nresult = {last_geo[-1]}\n"
                    else:
                        # Fallback: last assignment that isn't a known non-geometry var
                        all_assigns = _re.findall(r'^(\w+)\s*=', code, _re.MULTILINE)
                        candidates = [v for v in all_assigns
                                      if v not in _skip_vars
                                      and not v.startswith('_')
                                      and not v.isupper()]  # skip ALL_CAPS constants
                        if candidates:
                            code += f"\nresult = {candidates[-1]}\n"
                st.session_state.current_code = code
                with st.spinner("Building 3D preview... executing CadQuery code"):
                    mesh, err, cq_obj = execute_cadquery_code(code)
                if mesh:
                    st.session_state.preview_mesh = mesh
                    if cq_obj is not None:
                        st.session_state.faces_info = extract_faces_info(cq_obj)
                        st.session_state.edges_info = extract_edges_info(cq_obj)
                    if err is None:
                        ai_response += "\n\nCode executed successfully. The 3D preview has been updated."
                else:
                    ai_response += f"\n\nExecution error: {err}\nPlease describe what went wrong so I can fix it."

        # Add AI response to history (tagged with phase)
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response, "phase": ai_phase})
        st.rerun()


# ================================================================
#  RIGHT COLUMN - 3D PREVIEW
# ================================================================
with col_preview:
    # Dev Mode is now toggled from the top toolbar; just read its current state
    dev_mode = st.session_state.get("dev_mode", False)

    # -- Dev Mode: standalone code editor (skip all phases) --
    if dev_mode:
        st.markdown("<div class='section-label'>Dev Mode — Direct Code Editor</div>", unsafe_allow_html=True)
        st.caption("Paste or write CadQuery code below and click Run. No phases required.")
        default_code = st.session_state.current_code or (
            "import cadquery as cq\n\n"
            "# Parameters\n"
            "width = 50\nheight = 30\ndepth = 20\n\n"
            "# Build\n"
            "result = cq.Workplane('XY').box(width, height, depth)\n"
        )
        dev_code = st.text_area(
            "CadQuery Code",
            value=default_code,
            height=300,
            key="dev_code_editor",
            label_visibility="collapsed",
        )
        dev_run_col1, dev_run_col2 = st.columns([3, 1])
        with dev_run_col1:
            if st.button("Run", type="primary", use_container_width=True, key="dev_run"):
                st.session_state.current_code = dev_code
                with st.spinner("Executing CadQuery code..."):
                    mesh, err, cq_obj = execute_cadquery_code(dev_code)
                if mesh and len(mesh.vertices) > 0:
                    st.session_state.preview_mesh = mesh
                    if cq_obj is not None:
                        st.session_state.faces_info = extract_faces_info(cq_obj)
                        st.session_state.edges_info = extract_edges_info(cq_obj)
                    st.success("Preview updated.")
                    st.rerun()
                else:
                    st.error(f"Execution error: {err or 'Mesh is empty.'}")
        with dev_run_col2:
            if st.button("Clear Preview", use_container_width=True, key="dev_clear"):
                st.session_state.preview_mesh = None
                st.rerun()
        st.markdown("---")

    st.markdown("<div class='section-label'>3D Preview</div>", unsafe_allow_html=True)

    if st.session_state.preview_mesh is not None:
        mesh = st.session_state.preview_mesh

        if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
            st.error("Mesh is empty.")
        else:
            try:
                import plotly.graph_objects as go

                verts = mesh.vertices
                faces = mesh.faces

                # Build edge lines from mesh faces for visible wireframe
                import numpy as np
                edge_set = set()
                for f in faces:
                    for a, b in [(f[0], f[1]), (f[1], f[2]), (f[2], f[0])]:
                        edge_set.add((min(a, b), max(a, b)))
                xe, ye, ze = [], [], []
                for a, b in edge_set:
                    xe += [verts[a][0], verts[b][0], None]
                    ye += [verts[a][1], verts[b][1], None]
                    ze += [verts[a][2], verts[b][2], None]

                # --- Measurement mode selector ---
                faces_data = st.session_state.get("faces_info", [])
                edges_data = st.session_state.get("edges_info", [])
                has_meas = bool(faces_data or edges_data)
                selected_items = st.session_state.get("selected_meas_items", [])

                if has_meas:
                    mode_col1, mode_col2 = st.columns([3, 1])
                    with mode_col1:
                        meas_3d_mode = st.radio(
                            "Mode",
                            ["View", "Measure Faces", "Measure Edges"],
                            horizontal=True,
                            key="meas_3d_radio",
                            label_visibility="collapsed",
                        )
                    with mode_col2:
                        if selected_items and meas_3d_mode != "View":
                            if st.button("Clear Selection", key="clear_sel_btn", use_container_width=True):
                                st.session_state.selected_meas_items = []
                                st.rerun()
                    # Reset selection when switching modes
                    prev_mode = st.session_state.get("meas_3d_mode", "View")
                    if meas_3d_mode != prev_mode:
                        # Auto-select first two items when entering a measurement mode
                        if meas_3d_mode == "Measure Faces" and len(faces_data) >= 2:
                            st.session_state.selected_meas_items = [0, 1]
                        elif meas_3d_mode == "Measure Edges" and len(edges_data) >= 2:
                            st.session_state.selected_meas_items = [0, 1]
                        else:
                            st.session_state.selected_meas_items = []
                        selected_items = st.session_state.selected_meas_items
                    st.session_state.meas_3d_mode = meas_3d_mode

                    # --- Selection dropdowns ABOVE the chart ---
                    if meas_3d_mode == "Measure Faces" and faces_data:
                        dc1, dc2 = st.columns(2)
                        dd_labels = [f"F{i+1}: {f['label']}" for i, f in enumerate(faces_data)]
                        sel_a_idx = selected_items[0] if len(selected_items) > 0 and selected_items[0] < len(dd_labels) else 0
                        sel_b_idx = selected_items[1] if len(selected_items) > 1 and selected_items[1] < len(dd_labels) else min(1, len(dd_labels)-1)
                        with dc1:
                            da = st.selectbox("Face A", dd_labels, index=sel_a_idx, key="dd_face_a")
                        with dc2:
                            db = st.selectbox("Face B", dd_labels, index=sel_b_idx, key="dd_face_b")
                        ia = dd_labels.index(da)
                        ib = dd_labels.index(db)
                        if [ia, ib] != list(selected_items):
                            st.session_state.selected_meas_items = [ia, ib]
                            selected_items = [ia, ib]

                    elif meas_3d_mode == "Measure Edges" and edges_data:
                        dc1, dc2 = st.columns(2)
                        dd_labels = [f"E{i+1}: {e['label']}" for i, e in enumerate(edges_data)]
                        sel_a_idx = selected_items[0] if len(selected_items) > 0 and selected_items[0] < len(dd_labels) else 0
                        sel_b_idx = selected_items[1] if len(selected_items) > 1 and selected_items[1] < len(dd_labels) else min(1, len(dd_labels)-1)
                        with dc1:
                            da = st.selectbox("Edge A", dd_labels, index=sel_a_idx, key="dd_edge_a")
                        with dc2:
                            db = st.selectbox("Edge B", dd_labels, index=sel_b_idx, key="dd_edge_b")
                        ia = dd_labels.index(da)
                        ib = dd_labels.index(db)
                        if [ia, ib] != list(selected_items):
                            st.session_state.selected_meas_items = [ia, ib]
                            selected_items = [ia, ib]
                else:
                    meas_3d_mode = "View"

                # --- Face coloring ---
                FACE_PALETTE = [
                    '#a8d8ea', '#f3b0c3', '#c6e2b6', '#f9e4b7', '#cbb0f5', '#b8f0e0',
                    '#f5b0d4', '#d5f0b0', '#b0c8f1', '#f5d4b0', '#b0f0d4', '#e6b0f5',
                ]
                SEL_COLORS = ['#ff6b6b', '#ffd93d']

                facecolor_arr = None
                if faces_data and meas_3d_mode != "View":
                    # Use exact OCC face map if available, fall back to heuristic
                    tri_map_exact = mesh.metadata.get('tri_face_map') if hasattr(mesh, 'metadata') else None
                    if tri_map_exact is not None and len(tri_map_exact) == len(faces):
                        tri_map = tri_map_exact
                    else:
                        tri_map = map_triangles_to_cad_faces(verts, faces, faces_data)
                    facecolor_arr = [FACE_PALETTE[int(tri_map[i]) % len(FACE_PALETTE)]
                                     for i in range(len(faces))]
                    # Highlight selected faces
                    for sel_order, sel_idx in enumerate(selected_items[:2]):
                        if sel_idx < len(faces_data):
                            for ti in np.where(tri_map == sel_idx)[0]:
                                facecolor_arr[ti] = SEL_COLORS[min(sel_order, 1)]

                # --- Build figure ---
                fig = go.Figure()

                mesh_args = dict(
                    x=verts[:, 0].tolist(),
                    y=verts[:, 1].tolist(),
                    z=verts[:, 2].tolist(),
                    i=faces[:, 0].tolist(),
                    j=faces[:, 1].tolist(),
                    k=faces[:, 2].tolist(),
                    opacity=1.0,
                    flatshading=True,
                    lighting=dict(ambient=0.5, diffuse=0.7, specular=0.3, roughness=0.4),
                    lightposition=dict(x=100, y=200, z=300),
                )
                if facecolor_arr:
                    mesh_args['facecolor'] = facecolor_arr
                else:
                    mesh_args['color'] = '#b0d4f1'

                # Per-triangle hover for Measure Faces mode
                if meas_3d_mode == "Measure Faces" and faces_data and facecolor_arr is not None:
                    tri_hover = []
                    for ti in range(len(faces)):
                        fi_idx = int(tri_map[ti])
                        fi = faces_data[fi_idx]
                        sel_tag = ""
                        if fi_idx in selected_items:
                            sel_tag = " [SELECTED]"
                        tri_hover.append(
                            f"F{fi_idx+1}: {fi['type']}{sel_tag}<br>"
                            f"Area: {fi['area']:.1f} mm²<br>"
                            f"Center: ({fi['center'][0]:.1f}, {fi['center'][1]:.1f}, {fi['center'][2]:.1f})<br>"
                            f"Normal: ({fi['normal'][0]}, {fi['normal'][1]}, {fi['normal'][2]})"
                        )
                    mesh_args['hovertext'] = tri_hover
                    mesh_args['hoverinfo'] = 'text'
                else:
                    mesh_args['hoverinfo'] = 'skip'

                fig.add_trace(go.Mesh3d(**mesh_args))

                # Wireframe
                fig.add_trace(go.Scatter3d(
                    x=xe, y=ye, z=ze,
                    mode="lines",
                    line=dict(color="#1a1a2e", width=1.5),
                    hoverinfo="skip",
                    showlegend=False,
                ))

                # --- Clickable markers for measurement ---
                if meas_3d_mode == "Measure Faces" and faces_data:
                    m_colors = []
                    m_sizes = []
                    for i in range(len(faces_data)):
                        if i in selected_items:
                            m_colors.append(SEL_COLORS[min(selected_items.index(i), 1)])
                            m_sizes.append(12)
                        else:
                            m_colors.append('#ffffff')
                            m_sizes.append(7)
                    fig.add_trace(go.Scatter3d(
                        x=[f['center'][0] for f in faces_data],
                        y=[f['center'][1] for f in faces_data],
                        z=[f['center'][2] for f in faces_data],
                        mode='markers+text',
                        marker=dict(size=m_sizes, color=m_colors, symbol='circle',
                                    line=dict(width=1.5, color='#333'), opacity=0.95),
                        text=[f"F{i+1}" for i in range(len(faces_data))],
                        textposition="top center",
                        textfont=dict(size=10, color='#222'),
                        hovertext=[f['label'] for f in faces_data],
                        hoverinfo="text",
                        showlegend=False,
                    ))

                elif meas_3d_mode == "Measure Edges" and edges_data:
                    # Draw each CadQuery edge as a thick hoverable line along its full length
                    N_PTS = 20  # interpolation points per edge
                    for i, e in enumerate(edges_data):
                        sx, sy, sz = e['start']
                        ex, ey, ez = e['end']
                        xs = [sx + (ex - sx) * t / (N_PTS - 1) for t in range(N_PTS)]
                        ys = [sy + (ey - sy) * t / (N_PTS - 1) for t in range(N_PTS)]
                        zs = [sz + (ez - sz) * t / (N_PTS - 1) for t in range(N_PTS)]
                        if i in selected_items:
                            color = SEL_COLORS[min(selected_items.index(i), 1)]
                            width = 18
                        else:
                            color = FACE_PALETTE[i % len(FACE_PALETTE)]
                            width = 14
                        hover = (
                            f"E{i+1}: {e['type']}<br>"
                            f"Length: {e['length']:.2f} mm<br>"
                            f"({sx:.1f},{sy:.1f},{sz:.1f}) → ({ex:.1f},{ey:.1f},{ez:.1f})"
                        )
                        fig.add_trace(go.Scatter3d(
                            x=xs, y=ys, z=zs,
                            mode='lines+markers',
                            line=dict(color=color, width=width),
                            marker=dict(size=max(4, width // 3), color=color, opacity=0.01),
                            hovertext=[hover] * N_PTS,
                            hoverinfo='text',
                            showlegend=False,
                        ))
                    # Label markers at midpoints
                    mid_pts = [((e['start'][0]+e['end'][0])/2,
                                (e['start'][1]+e['end'][1])/2,
                                (e['start'][2]+e['end'][2])/2) for e in edges_data]
                    m_colors = []
                    m_sizes = []
                    for i in range(len(edges_data)):
                        if i in selected_items:
                            m_colors.append(SEL_COLORS[min(selected_items.index(i), 1)])
                            m_sizes.append(14)
                        else:
                            m_colors.append('#ffffff')
                            m_sizes.append(10)
                    fig.add_trace(go.Scatter3d(
                        x=[p[0] for p in mid_pts],
                        y=[p[1] for p in mid_pts],
                        z=[p[2] for p in mid_pts],
                        mode='markers+text',
                        marker=dict(size=m_sizes, color=m_colors, symbol='diamond',
                                    line=dict(width=2, color='#333'), opacity=0.95),
                        text=[f"E{i+1}" for i in range(len(edges_data))],
                        textposition="top center",
                        textfont=dict(size=11, color='#222', family='Arial Black'),
                        hoverinfo="skip",
                        showlegend=False,
                    ))

                # --- Visual distance line + overlay annotations ---
                _meas_result = None
                if len(selected_items) >= 2 and meas_3d_mode != "View":
                    if meas_3d_mode == "Measure Faces" and faces_data:
                        _meas_result = compute_face_face(
                            faces_data[selected_items[0]], faces_data[selected_items[1]])
                        pt_a = _meas_result['center_a']
                        pt_b = _meas_result['center_b']
                    elif meas_3d_mode == "Measure Edges" and edges_data:
                        _meas_result = compute_edge_edge(
                            edges_data[selected_items[0]], edges_data[selected_items[1]])
                        pt_a = _meas_result['closest_a']
                        pt_b = _meas_result['closest_b']
                    else:
                        pt_a = pt_b = None

                    if pt_a and pt_b:
                        mid = [(pt_a[i] + pt_b[i]) / 2 for i in range(3)]
                        dist_val = _meas_result.get('distance', 0)
                        fig.add_trace(go.Scatter3d(
                            x=[pt_a[0], pt_b[0]], y=[pt_a[1], pt_b[1]], z=[pt_a[2], pt_b[2]],
                            mode='lines+markers',
                            line=dict(color='#ff4444', width=5, dash='dash'),
                            marker=dict(size=5, color='#ff4444', symbol='x'),
                            hoverinfo='skip', showlegend=False,
                        ))
                        fig.add_trace(go.Scatter3d(
                            x=[mid[0]], y=[mid[1]], z=[mid[2]],
                            mode='text',
                            text=[f"{dist_val:.2f} mm"],
                            textfont=dict(size=13, color='#ff4444', family='Arial Black'),
                            textposition='top center',
                            hoverinfo='skip', showlegend=False,
                        ))

                    # Build overlay info text for the chart
                    if _meas_result:
                        meas = _meas_result
                        if meas_3d_mode == "Measure Faces":
                            label_a = f"F{selected_items[0]+1}"
                            label_b = f"F{selected_items[1]+1}"
                        else:
                            label_a = f"E{selected_items[0]+1}"
                            label_b = f"E{selected_items[1]+1}"

                        # Build property tags
                        props = []
                        for p in ['parallel', 'perpendicular', 'coplanar', 'intersecting']:
                            if meas.get(p):
                                props.append(p.capitalize())
                        if meas.get('facing'):
                            props.append(meas['facing'].capitalize())
                        if meas.get('shared_vertex'):
                            props.append("Shared vertex")
                        prop_str = " \u00b7 ".join(props) if props else ""

                        overlay_lines = [
                            f"<b>{label_a} \u2194 {label_b}</b>  \u2014  {meas['relation']}",
                        ]
                        if meas.get('distance') is not None:
                            overlay_lines.append(f"Distance: <b>{meas['distance']:.2f} mm</b>")
                        if meas.get('angle') is not None:
                            overlay_lines.append(f"Angle: <b>{meas['angle']:.2f}\u00b0</b>")
                        if prop_str:
                            overlay_lines.append(prop_str)

                        overlay_text = "<br>".join(overlay_lines)

                        fig.add_annotation(
                            text=overlay_text,
                            xref="paper", yref="paper",
                            x=0.5, y=0.98,
                            xanchor="center", yanchor="top",
                            showarrow=False,
                            font=dict(size=14, color="#ffffff", family="Arial"),
                            bgcolor="rgba(30, 30, 50, 0.85)",
                            bordercolor="#ff6b6b",
                            borderwidth=2,
                            borderpad=10,
                        )

                title_text = ("Select items above · Relationship shown on model"
                              if meas_3d_mode != "View"
                              else "Drag to rotate | Scroll to zoom | Right-click to pan")
                fig.update_layout(
                    scene=dict(
                        aspectmode="data",
                        xaxis_title="X (Right)",
                        yaxis_title="Y (Forward)",
                        zaxis_title="Z (Up)",
                    ),
                    height=700,
                    margin=dict(l=0, r=0, t=30, b=0),
                    title=dict(text=title_text, x=0.5, xanchor="center"),
                )
                config = {
                    "displayModeBar": True,
                    "toImageButtonOptions": {
                        "format": "png",
                        "filename": "model_screenshot",
                        "height": 700,
                        "width": 1200,
                        "scale": 2,
                    },
                    "modeBarButtonsToAdd": ["toImage"],
                }

                # --- Render chart with click-to-select ---
                if meas_3d_mode != "View":
                    from streamlit_plotly_events import plotly_events
                    import time as _time
                    clicked = plotly_events(
                        fig, click_event=True, select_event=False,
                        hover_event=False, override_height=700,
                        override_width="100%", key="preview_3d",
                    )
                    # Handle click on marker — deduplicate to avoid rerun loops
                    if clicked:
                        pt = clicked[0]
                        click_sig = f"{pt.get('curveNumber')}_{pt.get('pointIndex')}_{pt.get('x')}_{pt.get('y')}_{pt.get('z')}"
                        last_sig = st.session_state.get("_last_click_sig", "")

                        if click_sig != last_sig:
                            st.session_state._last_click_sig = click_sig
                            curve_idx = pt.get('curveNumber', None)
                            point_idx = pt.get('pointIndex', None)
                            clicked_item = None

                            print(f"[MEAS-DEBUG] Click event: curve={curve_idx} point={point_idx} sig={click_sig}")

                            if meas_3d_mode == "Measure Faces":
                                # trace 0=mesh, 1=wireframe, 2=face markers
                                if curve_idx == 2 and point_idx is not None:
                                    clicked_item = point_idx
                                    print(f"[MEAS-DEBUG] Mapped to Face F{clicked_item+1}")
                                else:
                                    print(f"[MEAS-DEBUG] Ignored click on trace {curve_idx} (not face markers)")
                            elif meas_3d_mode == "Measure Edges":
                                # trace 0=mesh, 1=wireframe, 2..N+1=edge lines, N+2=edge midpoint markers
                                n_edges = len(edges_data)
                                marker_trace = 2 + n_edges  # midpoint marker trace
                                if curve_idx == marker_trace and point_idx is not None:
                                    clicked_item = point_idx
                                    print(f"[MEAS-DEBUG] Clicked midpoint marker -> Edge E{clicked_item+1}")
                                elif 2 <= curve_idx < 2 + n_edges:
                                    clicked_item = curve_idx - 2
                                    print(f"[MEAS-DEBUG] Clicked edge line trace {curve_idx} -> Edge E{clicked_item+1}")
                                else:
                                    print(f"[MEAS-DEBUG] Ignored click on trace {curve_idx} (edges range 2..{2+n_edges-1}, markers={marker_trace})")

                            if clicked_item is not None:
                                cur_sel = list(st.session_state.get("selected_meas_items", []))
                                old_sel = list(cur_sel)
                                if clicked_item in cur_sel:
                                    cur_sel.remove(clicked_item)
                                elif len(cur_sel) < 2:
                                    cur_sel.append(clicked_item)
                                else:
                                    cur_sel = [cur_sel[-1], clicked_item]
                                print(f"[MEAS-DEBUG] Selection: {old_sel} -> {cur_sel}")
                                st.session_state.selected_meas_items = cur_sel
                                st.rerun()
                        else:
                            print(f"[MEAS-DEBUG] Duplicate click ignored: {click_sig}")
                else:
                    st.plotly_chart(fig, use_container_width=True, config=config, key="preview_3d")
            except ImportError:
                st.error("Plotly not installed. Run: pip install plotly")
            except Exception as e:
                st.error(f"Visualisation error: {e}")

        # Action bar
        if st.button("Refresh Preview", use_container_width=True, key="refresh_prev"):
            if st.session_state.current_code:
                with st.spinner("Regenerating..."):
                    mesh, err, cq_obj = execute_cadquery_code(st.session_state.current_code)
                    if mesh:
                        st.session_state.preview_mesh = mesh
                        if cq_obj is not None:
                            st.session_state.faces_info = extract_faces_info(cq_obj)
                            st.session_state.edges_info = extract_edges_info(cq_obj)
                        st.rerun()
                    else:
                        st.error(err)

        # Mesh info
        with st.expander("Mesh Information"):
            m = st.session_state.preview_mesh
            st.markdown(
                f"**Vertices:** {len(m.vertices):,}<br>"
                f"**Faces:** {len(m.faces):,}<br>"
                f"**Watertight:** {'Yes' if m.is_watertight else 'No'}<br>"
                f"**Volume:** {m.volume / 1000:.2f} cm3" if hasattr(m, 'volume') and m.is_watertight else
                f"**Vertices:** {len(m.vertices):,}<br>"
                f"**Faces:** {len(m.faces):,}<br>"
                f"**Watertight:** {'Yes' if m.is_watertight else 'No'}",
                unsafe_allow_html=True,
            )

        # ---- Measurement Tools ----
        with st.expander("Measurement Tools", expanded=False):
            faces_data = st.session_state.get("faces_info", [])
            edges_data = st.session_state.get("edges_info", [])
            if not faces_data and not edges_data:
                st.caption("Measurements require a CadQuery solid. Run or regenerate code first.")
            else:
                meas_mode = st.radio(
                    "Measure between",
                    ["Faces", "Edges"],
                    horizontal=True,
                    key="meas_mode",
                    label_visibility="collapsed",
                )
                if meas_mode == "Faces":
                    if not faces_data:
                        st.warning("No faces found on the solid.")
                    else:
                        labels = [f['label'] for f in faces_data]

                        # Single face info
                        st.markdown("**Select a face to inspect:**")
                        sel_single = st.selectbox("Face", labels, key="meas_face_single", label_visibility="collapsed")
                        idx_s = labels.index(sel_single)
                        fi = faces_data[idx_s]
                        st.markdown(
                            f"**Type:** {fi['type']}<br>"
                            f"**Center:** ({fi['center'][0]:.2f}, {fi['center'][1]:.2f}, {fi['center'][2]:.2f})<br>"
                            f"**Normal:** ({fi['normal'][0]}, {fi['normal'][1]}, {fi['normal'][2]})<br>"
                            f"**Area:** {fi['area']:.2f} mm²",
                            unsafe_allow_html=True,
                        )

                        st.markdown("---")
                        st.markdown("**Measure between two faces:**")
                        mcol1, mcol2 = st.columns(2)
                        with mcol1:
                            sel_a = st.selectbox("Face A", labels, key="meas_face_a")
                        with mcol2:
                            default_b = min(1, len(labels) - 1)
                            sel_b = st.selectbox("Face B", labels, index=default_b, key="meas_face_b")

                        idx_a = labels.index(sel_a)
                        idx_b = labels.index(sel_b)
                        if idx_a == idx_b:
                            st.info("Select two different faces to measure.")
                        else:
                            result = compute_face_face(faces_data[idx_a], faces_data[idx_b])
                            # Distance
                            st.markdown(f"**Distance:** {result['distance']:.2f} mm")
                            # Angle
                            if result['parallel']:
                                st.markdown(f"**Angle:** 0° (parallel faces)")
                            elif result['perpendicular']:
                                st.markdown(f"**Angle:** 90° (perpendicular faces)")
                            else:
                                st.markdown(f"**Angle:** {result['angle']:.2f}°")

                else:  # Edges
                    if not edges_data:
                        st.warning("No edges found on the solid.")
                    else:
                        labels = [e['label'] for e in edges_data]

                        # Single edge info
                        st.markdown("**Select an edge to inspect:**")
                        sel_single = st.selectbox("Edge", labels, key="meas_edge_single", label_visibility="collapsed")
                        idx_s = labels.index(sel_single)
                        ei = edges_data[idx_s]
                        st.markdown(
                            f"**Type:** {ei['type']}<br>"
                            f"**Length:** {ei['length']:.2f} mm<br>"
                            f"**Start:** ({ei['start'][0]:.2f}, {ei['start'][1]:.2f}, {ei['start'][2]:.2f})<br>"
                            f"**End:** ({ei['end'][0]:.2f}, {ei['end'][1]:.2f}, {ei['end'][2]:.2f})",
                            unsafe_allow_html=True,
                        )

                        st.markdown("---")
                        st.markdown("**Measure between two edges:**")
                        mcol1, mcol2 = st.columns(2)
                        with mcol1:
                            sel_a = st.selectbox("Edge A", labels, key="meas_edge_a")
                        with mcol2:
                            default_b = min(1, len(labels) - 1)
                            sel_b = st.selectbox("Edge B", labels, index=default_b, key="meas_edge_b")

                        idx_a = labels.index(sel_a)
                        idx_b = labels.index(sel_b)
                        if idx_a == idx_b:
                            st.info("Select two different edges to measure.")
                        else:
                            result = compute_edge_edge(edges_data[idx_a], edges_data[idx_b])
                            if result['distance'] is not None:
                                st.markdown(f"**Distance (midpoint–midpoint):** {result['distance']:.2f} mm")
                            if result['angle'] is not None:
                                st.markdown(f"**Angle:** {result['angle']:.2f}°")


    else:
        st.markdown(
            "<div class='preview-empty'>"
            "<p style='font-size:1rem; font-weight:500;'>No model yet</p>"
            "<p style='font-size:0.85rem;'>Start a conversation with the AI. Once you reach Phase 4 (Code Generation), the preview will appear here automatically.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        # If we have code but no preview, offer to generate
        if st.session_state.current_code:
            if st.button("Generate Preview", type="primary", use_container_width=True, key="gen_prev"):
                with st.spinner("Executing CadQuery code..."):
                    mesh, err, cq_obj = execute_cadquery_code(st.session_state.current_code)
                    if mesh:
                        st.session_state.preview_mesh = mesh
                        if cq_obj is not None:
                            st.session_state.faces_info = extract_faces_info(cq_obj)
                            st.session_state.edges_info = extract_edges_info(cq_obj)
                        st.rerun()
                    else:
                        st.error(err)

    # ---- Always-visible code editor (shows whenever code exists) ----
    if st.session_state.current_code:
        st.markdown("---")
        st.markdown("<div style='font-weight:600; margin-bottom:0.5rem;'>CadQuery Code Editor</div>", unsafe_allow_html=True)
        edited_code = st.text_area(
            "CadQuery Code",
            value=st.session_state.current_code,
            height=350,
            key="code_editor",
            label_visibility="collapsed",
        )
        run_col1, run_col2, run_col3 = st.columns([3, 1, 1])
        with run_col1:
            if st.button("Run Code", type="primary", use_container_width=True, key="run_edited_code"):
                st.session_state.current_code = edited_code
                with st.spinner("Building 3D preview..."):
                    mesh, err, cq_obj = execute_cadquery_code(edited_code)
                    if mesh:
                        st.session_state.preview_mesh = mesh
                        if cq_obj is not None:
                            st.session_state.faces_info = extract_faces_info(cq_obj)
                            st.session_state.edges_info = extract_edges_info(cq_obj)
                        st.rerun()
                    else:
                        st.error(f"Execution error: {err}")
        with run_col2:
            if st.button("Reset", use_container_width=True, key="reset_code"):
                st.rerun()
        with run_col3:
            if st.button("Export STL", use_container_width=True, key="export_stl_code"):
                if st.session_state.preview_mesh is not None:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
                        st.session_state.preview_mesh.export(tmp.name)
                        tmp.flush()
                        tpath = tmp.name
                    with open(tpath, "rb") as f:
                        st.download_button(
                            label="Download STL",
                            data=f.read(),
                            file_name="ai_model.stl",
                            mime="application/vnd.ms-pki.stl",
                            key="dl_stl_code",
                        )
                    os.unlink(tpath)
                else:
                    st.warning("Run the code first to generate a mesh.")


