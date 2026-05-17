# Simple 3D Printing App with AI Code Generation
# How to run this program:
# 1. Install basic requirements: pip install streamlit openai python-dotenv requests
# 2. Run: streamlit run app_simple.py

import streamlit as st
import time
import random
import os
import tempfile
import subprocess
from pathlib import Path

# Try to import the API handler, but work without it if needed
try:
    from api_handler_simple import generate_geometry_code, refine_geometry_code
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    st.warning("AI API not available. Running in demo mode.")

# Function to execute Python code and return mesh for interactive preview
def execute_python_code(code):
    """Execute Python/trimesh code and return the mesh object"""
    try:
        import trimesh
        import numpy as np
        import re
        
        print(f"Executing Python code to generate mesh...")
        
        # Fix common issues with the code before execution
        # Issue 1: align_vectors returns 4x4 but code tries to assign to 3x3
        if 'align_vectors' in code and '[:3, :3]' in code:
            print("Detected align_vectors with 3x3 assignment - fixing to use full 4x4 matrix...")
            # Replace pattern: t[:3, :3] = align_vectors(...) with t = align_vectors(...)
            code = re.sub(
                r'(\w+)\[:3,\s*:3\]\s*=\s*trimesh\.geometry\.align_vectors',
                r'\1 = trimesh.geometry.align_vectors',
                code
            )
            # Remove the separate translation line if we're now using full matrix
            # Actually, we need a different approach - let's convert align_vectors to rotation_matrix
            
        # Better fix: Replace align_vectors with proper rotation_matrix usage
        if 'trimesh.geometry.align_vectors' in code:
            print("Detected align_vectors usage - this may cause issues. Attempting to fix...")
            # This is a complex fix, so let's just warn the user for now
            # The AI should learn to not use this function from the updated prompt
        
        # Execute the Python code in a controlled namespace
        namespace = {
            'trimesh': trimesh,
            'np': np,
            '__builtins__': __builtins__
        }
        
        # Execute the code
        exec(code, namespace)
        
        # Get the mesh from the namespace
        if 'mesh' not in namespace:
            return None, "Error: Python code must create a 'mesh' variable with the final trimesh object"
        
        mesh = namespace['mesh']
        
        if not isinstance(mesh, trimesh.Trimesh):
            return None, f"Error: 'mesh' variable must be a trimesh.Trimesh object, got {type(mesh)}"
        
        print(f"Mesh created successfully: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
        return mesh, None
            
    except ImportError as e:
        return None, f"Missing required library: {str(e)}. Please install trimesh and numpy."
    except ValueError as e:
        error_msg = str(e)
        if "could not broadcast" in error_msg and "shape" in error_msg:
            return None, f"Code generation error: Incompatible matrix dimensions (align_vectors issue). Please try regenerating or refining the model. Technical: {error_msg}"
        return None, f"Value error: {error_msg}"
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Exception: {error_details}")
        print(f"Code that failed:\n{code}")
        return None, f"Error during execution: {str(e)}\n\nCheck the console for the full code and error details."

# Function to export Python code to STL file
def export_to_stl(code):
    """Convert Python/trimesh code to STL file for 3D printing"""
    try:
        import trimesh
        
        print(f"Executing Python code to generate mesh for STL export...")
        
        # Execute the code and get the mesh
        mesh, error = execute_python_code(code)
        
        if error:
            return None, error
        
        # Create temporary STL file
        temp_dir = tempfile.gettempdir()
        stl_path = os.path.join(temp_dir, f"model_{int(time.time())}.stl")
        
        # Export to STL
        mesh.export(stl_path)
        
        print(f"STL file: {stl_path}")
        
        # Check if STL was created and has content
        if os.path.exists(stl_path):
            file_size = os.path.getsize(stl_path)
            print(f"STL created! Size: {file_size} bytes")
            
            if file_size > 0:
                # Read STL file as bytes for download
                with open(stl_path, 'rb') as f:
                    stl_data = f.read()
                
                # Clean up temp file
                try:
                    os.unlink(stl_path)
                except:
                    pass
                
                return stl_data, None
            else:
                return None, "STL file was created but is empty (0 bytes)"
        else:
            return None, "STL file not created"
            
    except ImportError as e:
        return None, f"Missing required library: {str(e)}. Please install trimesh and numpy."
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Exception: {error_details}")
        print(f"Code that failed:\n{code}")
        return None, f"Error during STL export: {str(e)}\n\nCheck the console for the full code and error details."

# Simple functions for demo mode
def demo_generate_code(description, dimensions=None, image_data=None):
    """Generate demo OpenSCAD code"""
    if dimensions:
        w, h, d = dimensions['width'], dimensions['height'], dimensions['depth']
    else:
        w, h, d = 100, 60, 80
    
    # Add image-based features in demo mode
    image_features = ""
    if image_data:
        image_features = """
// Features detected from uploaded image:
// - Adding decorative elements
translate([0, 0, height/2 + 2])
cylinder(r=5, h=4, center=true);
"""
    
    code = f"""// Generated 3D model: {description}
// Dimensions: {w}mm x {h}mm x {d}mm

width = {w};
height = {h};
depth = {d};

// Main object
cube([width, height, depth], center=true);

// Add some details based on description
// Rounded corners (if mentioned)
if (true) {{ // Simplified condition for demo
    translate([width/3, height/3, depth/2 + 1])
    cylinder(r=3, h=2, center=true);
}}{image_features}
"""
    return code, str(random.randint(1000, 9999))

# Set up the main page
st.title("AI 3D Model Generator")
st.write("Generate Python/trimesh code for 3D models using AI vision and text understanding")

if not API_AVAILABLE:
    st.warning("Running in demo mode. Set up your OpenAI API key for full functionality.")

# Initialize session state
if "current_code" not in st.session_state:
    st.session_state.current_code = ""
if "current_model_id" not in st.session_state:
    st.session_state.current_model_id = None
if "workflow_step" not in st.session_state:
    st.session_state.workflow_step = 1  # 1=Create, 2=Preview/Edit, 3=Export

# Progress indicator
steps = ["Create", "Preview & Edit", "Export"]
current_step = st.session_state.workflow_step
cols = st.columns(3)
for i, step_name in enumerate(steps, 1):
    with cols[i-1]:
        if i < current_step:
            st.success(f"✓ {step_name}")
        elif i == current_step:
            st.info(f"→ {step_name}")
        else:
            st.text(f"○ {step_name}")

st.divider()

# ============== STEP 1: CREATE MODEL ==============
if st.session_state.workflow_step == 1:
    st.header("Create 3D Model")
    
    # Get what they want to make
    user_description = st.text_area(
        "Description:", 
        placeholder="Example: A rectangular box with rounded corners and mounting holes, or an L-shaped elbow connector",
        height=120,
        help="Describe the shape, dimensions, features, and purpose of your model"
    )
    
    # Image upload section
    st.subheader("Reference Images (Optional)")

    uploaded_images = st.file_uploader(
        "Choose one or more image files", 
        type=['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'],
        accept_multiple_files=True,
        help="Upload images to help the AI understand what you want to create. Multiple angles or examples work best!"
    )
    
    # Show uploaded images
    images_data = []
    if uploaded_images:
        st.write(f"{len(uploaded_images)} image(s) uploaded:")
        cols = st.columns(min(len(uploaded_images), 3))
        for idx, img in enumerate(uploaded_images):
            with cols[idx % 3]:
                st.image(img, caption=f"{img.name}", width=200)
            # Read image data for API
            img_bytes = img.read()
            images_data.append(img_bytes)
            img.seek(0)  # Reset file pointer
        st.success(f"{len(uploaded_images)} image(s) ready for AI analysis")
    
    # For backward compatibility with single image references
    uploaded_image = uploaded_images[0] if uploaded_images else None
    image_data = images_data if images_data else None
    
    # Set default dimensions (no sliders needed for now)
    dimensions = None
    
    # Generate button
    if st.button("Generate 3D Model Code", type="primary"):
        if user_description or uploaded_images:
            # Show different messages based on what was provided
            if uploaded_images and user_description:
                img_count = len(uploaded_images)
                spinner_text = f"Analyzing {img_count} image{'s' if img_count > 1 else ''} and description to generate code..."
            elif uploaded_images:
                img_count = len(uploaded_images)
                spinner_text = f"Analyzing {img_count} image{'s' if img_count > 1 else ''} to generate code..."
            else:
                spinner_text = "Generating 3D model code..."
                
            with st.spinner(spinner_text):
                if API_AVAILABLE:
                    try:
                        code, model_id = generate_geometry_code(user_description, image_data, dimensions)
                        
                        # Check if image analysis worked
                        if uploaded_image and code:
                            if "unable to view" in code.lower() or "cannot see" in code.lower():
                                st.warning("Image was uploaded but AI vision is not available with your current plan. Generated code based on description only.")
                            elif "vision analysis is not available" in code.lower():
                                st.warning("Vision analysis not available - generated enhanced code based on description.")
                            else:
                                st.info("Image analysis may have been used in code generation.")
                    except Exception as e:
                        st.error(f"API Error: {str(e)}")
                        code, model_id = None, None
                else:
                    time.sleep(2)  # Simulate processing
                    code, model_id = demo_generate_code(user_description, dimensions, image_data)
                
                if code:
                    st.session_state.current_code = code
                    st.session_state.current_model_id = model_id
                    st.session_state.original_description = user_description
                    st.session_state.uploaded_images = uploaded_images  # Store all images
                    
                    # Show success message with details
                    if uploaded_images:
                        img_count = len(uploaded_images)
                        st.success(f"Code generated successfully using {img_count} image{'s' if img_count > 1 else ''} and description.")
                    else:
                        st.success("Code generated successfully.")
                    
                    # Move to next step
                    st.session_state.workflow_step = 2
                    st.rerun()
                else:
                    st.error("Failed to generate code. Please try again.")
        else:
            st.error("Please provide either a description or upload at least one image!")
    
    # If a model already exists, show Next button
    if st.session_state.current_code:
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Next: Preview Model", type="secondary", use_container_width=True):
                st.session_state.workflow_step = 2
                st.rerun()

# ============== STEP 2: PREVIEW & EDIT ==============
elif st.session_state.workflow_step == 2:
    if not st.session_state.current_code:
        st.warning("No model generated yet. Returning to step 1...")
        st.session_state.workflow_step = 1
        st.rerun()
    else:
        st.header("Interactive 3D Preview")
        
        # Show reference images if available (compact view)
        if "uploaded_images" in st.session_state and st.session_state.uploaded_images:
            with st.expander(f"Reference Images Used ({len(st.session_state.uploaded_images)})", expanded=False):
                # Display images in a compact grid
                img_count = len(st.session_state.uploaded_images)
                cols_per_row = 4  # Show 4 images per row for compact layout
                
                for row_start in range(0, img_count, cols_per_row):
                    row_imgs = st.session_state.uploaded_images[row_start:row_start + cols_per_row]
                    cols = st.columns(len(row_imgs))
                    for idx, img in enumerate(row_imgs):
                        with cols[idx]:
                            st.image(img, use_column_width=True, caption=f"#{row_start + idx + 1}")
        
        
        # Add a button to generate preview
        if st.button("Generate 3D Preview", type="primary"):
            with st.spinner("Generating 3D model..."):
                mesh, error = execute_python_code(st.session_state.current_code)
                
                if mesh:
                    st.session_state.preview_mesh = mesh
                    st.success(f"Model generated! {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
                    
                    # Debug: Show more details
                    st.write(f"Debug - Mesh bounds: {mesh.bounds}")
                    st.write(f"Debug - Mesh type: {type(mesh)}")
                    
                    # Clear any previous error
                    if "preview_error" in st.session_state:
                        del st.session_state.preview_error
                    
                    st.rerun()  # Refresh to show the preview
                else:
                    # Store the error for display
                    st.session_state.preview_error = error
                    st.error(f"{error}")
                    
                    # Check if this is the align_vectors error
                    if "align_vectors issue" in error or "could not broadcast" in error:
                        st.warning("� **Quick Fix Available:** This is a known code generation issue.")
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("Auto-Fix Code", type="secondary", use_container_width=True):
                                with st.spinner("Asking AI to fix the code..."):
                                    # Import the refine function
                                    from api_handler_simple import refine_geometry_code
                                    
                                    fix_instructions = "CRITICAL FIX NEEDED: Replace ALL uses of trimesh.geometry.align_vectors() with trimesh.transformations.rotation_matrix(). Use only 4x4 transformation matrices. Do not assign rotation matrices to [:3, :3] slices."
                                    
                                    new_code, new_model_id = refine_geometry_code(
                                        st.session_state.current_code,
                                        fix_instructions,
                                        st.session_state.current_model_id
                                    )
                                    
                                    if new_code:
                                        st.session_state.current_code = new_code
                                        st.session_state.current_model_id = new_model_id
                                        st.success("Code automatically fixed! Click 'Generate 3D Preview' again.")
                                        st.rerun()
                                    else:
                                        st.error("Auto-fix failed. Please try manual refinement below.")
                        
                        with col2:
                            st.info("Or use the refinement section below to manually describe changes")
                    
                    with st.expander("View Generated Code"):
                        st.code(st.session_state.current_code, language="python")
                        
                    # Show debugging button
                    if st.button("🔬 Debug - Show Raw Mesh Data"):
                        st.write("Error occurred, no mesh data available")
                        st.write("Error details:", error)
        
        # Display interactive 3D preview if available
        if "preview_mesh" in st.session_state and st.session_state.preview_mesh is not None:
            try:
                mesh = st.session_state.preview_mesh
                
                # Debug: Show mesh info
                st.info(f"Mesh Info: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces | Watertight: {'✅' if mesh.is_watertight else '❌'}")
                
                # Verify mesh has data
                if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
                    st.error("Mesh is empty - no vertices or faces to display")
                else:
                    # Extract vertex coordinates
                    vertices = mesh.vertices
                    faces = mesh.faces
                    
                    # Interactive 3D viewer with plotly
                    st.subheader("Interactive 3D View")
                    try:
                        import plotly.graph_objects as go
                        
                        # Create plotly figure with mesh
                        fig = go.Figure(data=[
                            go.Mesh3d(
                                x=vertices[:, 0].tolist(),
                                y=vertices[:, 1].tolist(),
                                z=vertices[:, 2].tolist(),
                                i=faces[:, 0].tolist(),
                                j=faces[:, 1].tolist(),
                                k=faces[:, 2].tolist(),
                                color='lightblue',
                                opacity=1.0,
                                flatshading=False
                            )
                        ])
                        
                        # Clean layout for interactive viewing
                        fig.update_layout(
                            scene=dict(
                                aspectmode='data'
                            ),
                            height=700,
                            margin=dict(l=0, r=0, t=30, b=0),
                            title=dict(
                                text="Drag to rotate • Scroll to zoom • Right-click to pan",
                                x=0.5,
                                xanchor='center'
                            )
                        )
                        
                        # Display the interactive plot
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
                    except Exception as plotly_error:
                        st.error(f"Visualization error: {plotly_error}")
                
                # Show mesh info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Vertices", f"{len(mesh.vertices):,}")
                with col2:
                    st.metric("Faces", f"{len(mesh.faces):,}")
                with col3:
                    if mesh.is_watertight:
                        st.metric("Status", "Watertight")
                    else:
                        st.metric("Status", "Not watertight")
                
            except ImportError:
                st.error("Plotly not installed. Run: pip install plotly")
            except Exception as e:
                st.error(f"Error displaying preview: {str(e)}")
        else:
            st.info("👆 Click 'Generate 3D Preview' to visualize your model")
        
        # Refinement section
        st.divider()
        st.subheader("✏️ Edit Model (Optional)")
        
        refinement = st.text_area(
            "What changes would you like to make?",
            placeholder="Example: Add mounting holes, make corners more rounded, increase the bend radius",
            height=100,
            key="refinement_input"
        )
        
        if st.button("Apply Changes", type="primary"):
            if refinement:
                with st.spinner("Refining your model..."):
                    if API_AVAILABLE:
                        refined_code, _ = refine_geometry_code(
                            st.session_state.current_model_id,
                            refinement,
                            None,
                            st.session_state.current_code
                        )
                    else:
                        time.sleep(1)
                        refined_code = st.session_state.current_code + f"\n# Refinement: {refinement}\n"
                    
                    if refined_code:
                        st.session_state.current_code = refined_code
                        # Clear preview so it regenerates
                        if "preview_mesh" in st.session_state:
                            del st.session_state.preview_mesh
                        st.success("Model refined! Click 'Generate 3D Preview' to see changes.")
                        st.rerun()
                    else:
                        st.error("Failed to refine model.")
            else:
                st.warning("Please describe the changes you want to make.")
        
        # Navigation buttons
        st.divider()
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        with col_nav1:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.workflow_step = 1
                st.rerun()
        with col_nav3:
            if st.button("Next ➡️", type="primary", use_container_width=True):
                st.session_state.workflow_step = 3
                st.rerun()

# ============== STEP 3: EXPORT ==============
elif st.session_state.workflow_step == 3:
    if not st.session_state.current_code:
        st.warning("No model generated yet. Returning to step 1...")
        st.session_state.workflow_step = 1
        st.rerun()
    else:
        st.header("Export & Download")
        
        # Show code
        st.subheader("Generated Python Code")
        with st.expander("View Full Code", expanded=False):
            st.code(st.session_state.current_code, language="python")
        
        col1, col2 = st.columns(2)
        with col1:
            # Download Python file
            st.download_button(
                "Download Python File",
                st.session_state.current_code,
                "model.py",
                "text/plain",
                help="Download the Python code to run locally or edit",
                use_container_width=True
            )
        with col2:
            # Show download button if STL is available
            if "stl_data" in st.session_state and st.session_state.stl_data:
                st.download_button(
                    "Download STL File",
                    st.session_state.stl_data,
                    "model.stl",
                    "application/octet-stream",
                    help="Download the STL file for slicing and 3D printing",
                    use_container_width=True
                )
        
        # STL Export section
        st.divider()
        st.subheader("Export to STL for 3D Printing")
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            if st.button("Generate STL File", type="primary", use_container_width=True):
                # Check if we have a preview mesh already
                if "preview_mesh" in st.session_state and st.session_state.preview_mesh is not None:
                    with st.spinner("Exporting preview mesh to STL..."):
                        try:
                            import trimesh
                            import tempfile
                            import os
                            import time
                            
                            mesh = st.session_state.preview_mesh
                            
                            # Create temporary STL file
                            temp_dir = tempfile.gettempdir()
                            stl_path = os.path.join(temp_dir, f"model_{int(time.time())}.stl")
                            
                            # Export to STL
                            mesh.export(stl_path)
                            
                            # Read STL file as bytes for download
                            with open(stl_path, 'rb') as f:
                                stl_data = f.read()
                            
                            # Clean up temp file
                            try:
                                os.unlink(stl_path)
                            except:
                                pass
                            
                            st.session_state.stl_data = stl_data
                            st.success(f"STL file generated from preview! ({len(stl_data)} bytes)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Export error: {str(e)}")
                else:
                    st.warning("Please generate a preview first (Step 2) before exporting to STL")
        
        with col_export2:
            # Show download button if STL is available
            if "stl_data" in st.session_state and st.session_state.stl_data:
                st.download_button(
                    "Download STL File",
                    st.session_state.stl_data,
                    "model.stl",
                    "application/octet-stream",
                    help="Download the STL file for slicing and 3D printing"
                )
        
        # STL info
        if "stl_data" in st.session_state and st.session_state.stl_data:
            st.success(f"STL ready! File size: {len(st.session_state.stl_data):,} bytes")
            st.info("""
            **Next steps:**
            1. Download the STL file above
            2. Open in your slicer (Cura, PrusaSlicer, etc.)
            3. Configure print settings (layer height, infill, supports)
            4. Slice and save G-code
            5. Send to your 3D printer!
            """)
        
        # Navigation buttons
        st.divider()
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        with col_nav1:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.workflow_step = 2
                st.rerun()
        with col_nav2:
            if st.button("🔄 Start New Model", use_container_width=True):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.workflow_step = 1
                st.rerun()
        
        # Model info
        if st.session_state.current_model_id:
            st.caption(f"Model ID: {st.session_state.current_model_id}")

# Footer
st.divider()
st.markdown("""
**Tips:**
- Use the Progress Indicator at the top to see where you are in the workflow
- The AI generates Python code using the trimesh library
- You can refine the model multiple times in the Preview step
- Use the interactive 3D preview to inspect your model from all angles before exporting
""")

if API_AVAILABLE:
    st.success("AI-powered code generation is active!")
else:
    st.warning("Install required packages for AI features: `pip install openai python-dotenv`")