import streamlit as st
import cv2 as cv
import pandas as pd
import numpy as np
from PIL import Image
import io
from io import BytesIO
from streamlit_image_zoom import image_zoom
import base64

# custom functions
# ------------------------------------------------------------
def submission_viewer(
    img_uri: str,
    height: int = 700,
    max_zoom_ratio: float = 4.0,
    key: str = "osd_viewer",
):
    html_template = """
    <!DOCTYPE html>
    <html style="height:100%">
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/openseadragon.min.js"></script>
        <style>
            body {
                margin: 0;
                padding: 0;
                background-color: #F5F5DC;
                height: 100%;
                width: 100%;
                overflow: hidden;
            }
            #openseadragon-container {
                width: 100vw;
                height: 100vh;
                background: #F5F5DC;
                border: 10px solid #374151;
                border-radius: 8px;
                box-sizing: border-box;
            }
        </style>
    </head>
    <body>
        <div id="openseadragon-container"></div>
        <script type="text/javascript">
            var viewer = OpenSeadragon({
                id: "openseadragon-container",
                prefixUrl: "https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/images/",
                tileSources: {
                    type: 'image',
                    url: '__IMAGE_URI__'
                },
                // Performance and Zoom configuration
                maxZoomPixelRatio: __MAX_ZOOM__,
                minZoomImageRatio: 0.8,
                visibilityRatio: 0.8,
                constrainDuringPan: true,
                
                // Controls setup
                showNavigationControl: true,
                navigationControlAnchor: OpenSeadragon.ControlAnchor.TOP_LEFT,
                showRotationControl: false,
                showFullPageControl: true,
                showHomeControl: true,
                
                // Smooth interaction tuning
                animationTime: 0.3,
                blendTime: 0.1,
                springStiffness: 10
            });

            // Zoom to question block once viewer finishes opening
            viewer.addHandler('open', function() {
                var answer_block = new OpenSeadragon.Rect(0.065396,0.108961, 0.199762, 0.311153);
                viewer.viewport.fitBounds(answer_block, true);
            });
        </script>
    </body>
    </html>
    """

    html_osd = html_template.replace("__IMAGE_URI__", img_uri).replace(
        "__MAX_ZOOM__", str(max_zoom_ratio)
    )

    st.iframe(html_osd, height=height)

def clear_files():
     st.session_state["uploader_key"] += 1
     del st.session_state["script_index"]

def next_submission():
    st.session_state["script_index"] += 1
    st.session_state["emplid"] = ""
    st.session_state["surname_field"] = ""
    st.session_state["name_field"] = ""
    st.rerun()

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    /* 1. Add Tuks Red border strip across the top of the app */
    header[data-testid="stHeader"] {
        border-top: 5px solid #D12631 !important;
    }

    /* 2. Style primary headers with UP Navy Blue */
    h1, h2, h3 {
        color: #002B49 !important;
    }

    /* 3. Style Sidebar header with a Gold bottom accent */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
        border-bottom: 2px solid #E8A800;
        padding-bottom: 5px;
    }

    /* Custom utility classes */
    .tuks-red { color: #D12631; font-weight: bold; }
    .up-gold { color: #E8A800; font-weight: bold; }
    </style>
""",
    unsafe_allow_html=True,
)

if "script_index" not in st.session_state:
    st.session_state["script_index"] = 0

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 100

if "aruco_key" not in st.session_state:
    st.session_state["aruco_key"] = 200

title_col1, title_col2= st.columns(2)
with title_col1:
    st.image("NAS_Faculty Logo.jpg")

with title_col2:
    st.title("GGY 168 — Introduction to Physical Geography")
    st.header("Submission Renaming Tool")

with st.expander("Instructions", expanded = False):
    st.markdown("""
    1. Load problematic asessment.
    2. Load the csv file containing the coordinates of the bubbles.
    3. Load the csv file containing the aruco coordinates.
    """)

with st.sidebar:
    uploaded_files = st.file_uploader("Select the student submission",
                         type = ["png"],
                         accept_multiple_files = True,
                         key = str(st.session_state["uploader_key"]))

    st.button("Clear", on_click = clear_files)

if uploaded_files:
    total_scripts = len(uploaded_files)
    image_file = uploaded_files[st.session_state["script_index"]]
    filename = image_file.name
    image_file.seek(0)
    
    #img = Image.open(image)

    # store the submission in memory as cv2 object
    img_bytes = np.frombuffer(image_file.getvalue(), dtype=np.uint8)
    cv_img = cv.imdecode(img_bytes, cv.IMREAD_COLOR)

    if cv_img is None:
        try:
            pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            cv_img = cv.cvtColor(np.array(pil_img), cv.COLOR_RGB2BGR)
        except Exception as e:
            st.error(f"Failed to read image file '{filename}': {e}")
            cv_img = None

    if cv_img is not None:
        processed_img = cv.imencode(".png",cv_img)[1]
        b64_str = base64.b64encode(processed_img).decode("utf-8")
        img_url = f"data:image/png;base64,{b64_str}"

    col1, col2 = st.columns(2)

    with col1:
        submission_viewer(img_url)
    
    with col2:
        snumber = st.text_input("Student Number", key="emplid")
        if st.button("Load Details"):
            df = pd.read_csv("class-list.csv", encoding = "latin1")
            surname, name = df.loc[df["emplid"] == snumber, ["surname", "name"]].iloc[0]
            sname = st.text_input("Surname", value=surname, key="surname_field")
            fname = st.text_input("Initials", value=name, key="name_field")
            filename = f"{surname}_{name}_{snumber}.png"
            final_img_rgb = cv.cvtColor(cv_img, cv.COLOR_BGR2RGB)
            final_img_pil = Image.fromarray(final_img_rgb)
            buffer = io.BytesIO()
            final_img_pil.save(buffer, format="PNG")
            st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="image/png")

        if st.button("Unknown student"):
            filename = f'unknown_{st.session_state["script_index"]}.png'
            final_img_rgb = cv.cvtColor(cv_img, cv.COLOR_BGR2RGB)
            final_img_pil = Image.fromarray(final_img_rgb)
            buffer = io.BytesIO()
            final_img_pil.save(buffer, format="PNG")
            st.download_button(label=f"Download {filename}", data=buffer, file_name=filename, mime="image/png")

        if st.session_state["script_index"] < len(uploaded_files) - 1:
            st.button("Next Submission", on_click = next_submission)
