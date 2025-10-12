# My 3D Printing App
# How to run this program:
# 1. Make sure you installed streamlit by typing: pip install streamlit
# 2. Run the program by typing: streamlit run app_simplified.py
# 3. The website will open in your browser!

import streamlit as st  # this is for making the website
import time  # this is for adding delays
import random  # this helps us make random numbers for testing

# Making fake functions that pretend to do stuff (because we don't have a real 3D printer yet)
def make_3d_model(what_to_make, picture=None):
    # wait a bit to make it look like it's thinking
    time.sleep(1)
    
    # make a random model ID using numbers
    model_id = str(random.randint(1000, 9999))
    return {
        "model_id": model_id,
        "preview": None  # we don't have real previews yet
    }

def change_model(model_id, changes, size):
    # pretend to change the model
    time.sleep(1)
    return True

def prepare_for_printer(model_id, which_printer, what_material):
    # pretend to prepare the file for printing
    time.sleep(1)
    job_id = str(random.randint(1000, 9999))
    
    # check if they want a STEP file
    if "STEP" in what_material.upper():
        file_type = "step"
    else:
        file_type = "stl"
    
    return {
        "job_id": job_id,
        "file_type": file_type
    }

def get_printable_file(job_id, file_type):
    # this would normally give us a real 3D model file
    # but for now we'll just return some text
    time.sleep(1)
    return f"This would be a {file_type} file (job {job_id})".encode()

# Set up the main page
st.title("My 3D Printing App")
st.write("This app helps you make 3D models for printing!")

# Make tabs for each step
current_step = st.radio("Choose what to do:", 
    ["1. Make a model", "2. Change the model", "3. Get the file"])

# Step 1: Making the model
if current_step == "1. Make a model":
    st.header("Make your 3D model")
    
    # Get what they want to make
    user_idea = st.text_area("What do you want to make?", 
        placeholder="Example: A box that is 10cm wide")
    
    # Let them upload a picture
    picture = st.file_uploader("Upload a picture if you want:", type=["png", "jpg"])
    
    # Button to make the model
    if st.button("Create my model!"):
        if user_idea or picture:  # check if they gave us something to work with
            result = make_3d_model(user_idea, picture)
            st.session_state["model_id"] = result["model_id"]
            st.success(f"Made your model! (ID: {result['model_id']})")
        else:
            st.error("Please tell me what to make first!")

# Step 2: Changing the model
elif current_step == "2. Change the model":
    st.header("Change your model")
    
    # Check if they made a model first
    if "model_id" not in st.session_state:
        st.error("Please make a model in step 1 first!")
    else:
        # Get the size they want
        width = st.slider("Width (mm)", 5, 400, 100)
        height = st.slider("Height (mm)", 5, 400, 60)
        depth = st.slider("Depth (mm)", 5, 400, 80)
        
        # Get any changes they want to make
        changes = st.text_area("What changes do you want to make?",
            placeholder="Example: Make the corners more rounded")
        
        # Let them pick a printer
        printer = st.selectbox("Which printer?", 
            ["Any printer", "Ultimaker S5", "Prusa MK4", "Bambu Lab X1C"])
        
        # Let them pick the material
        material = st.selectbox("What material?", [
            "Normal PLA",
            "Strong PLA",
            "PETG",
            "ABS (needs enclosure)",
            "STEP file (no printing)"
        ])
        
        # Button to apply changes and prepare for printing
        if st.button("Prepare for printing!"):
            # First make any changes they wanted
            change_model(st.session_state["model_id"], changes, 
                        {"width": width, "height": height, "depth": depth})
            
            # Then prepare it for the printer
            result = prepare_for_printer(st.session_state["model_id"], 
                                      printer, material)
            
            st.session_state["job_id"] = result["job_id"]
            st.session_state["file_type"] = result["file_type"]
            st.success("Your model is ready to download!")

# Step 3: Getting the file
elif current_step == "3. Get the file":
    st.header("Download your file")
    
    # Check if they prepared a file
    if "job_id" not in st.session_state:
        st.error("Please prepare your model in step 2 first!")
    else:
        # Let them pick the file type
        file_type = st.radio("Pick your file type:", 
            ["stl", "step", "obj"])
        
        # Button to download
        if st.button("Get my file"):
            # Get the file data
            file_data = get_printable_file(st.session_state["job_id"], 
                                         file_type)
            
            # Make the download button
            st.download_button(
                "Download your model!",
                file_data,
                f"my_model.{file_type}",
                "application/octet-stream"
            )

# Add some helpful notes at the bottom
st.write("---")
st.write("Note: This is just a demo - it doesn't make real 3D models yet.")