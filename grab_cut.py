import cv2
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# Caching to load image only once
@st.cache_data
def load_image(uploaded_file):
    image = Image.open(uploaded_file)
    return np.array(image)

# Reduce image size to improve processing speed
@st.cache_data
def resize_image(image, max_dim=800):
    height, width = image.shape[:2]
    if max(height, width) > max_dim:
        scaling_factor = max_dim / float(max(height, width))
        new_size = (int(width * scaling_factor), int(height * scaling_factor))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
    return image

# Function to apply GrabCut algorithm
@st.cache_data
def apply_grabcut(image, rect):
    mask = np.zeros(image.shape[:2], np.uint8)
    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)
    cv2.grabCut(image, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    return image * mask2[:, :, np.newaxis]

# Main Streamlit app
st.title("Optimized Background Remover using GrabCut")

# Upload an image
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Load and resize image
    image_np = load_image(uploaded_file)
    image_np = resize_image(image_np)

    # Display the uploaded image
    st.image(image_np, caption="Original Image", use_column_width=True)

    # Set canvas parameters
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=3,
        stroke_color="rgba(255, 0, 0, 1)",
        background_image=Image.fromarray(image_np),
        update_streamlit=True,
        height=image_np.shape[0],
        width=image_np.shape[1],
        drawing_mode="rect",  # Allow only rectangle drawing
        key="canvas",
    )

    # Check if a rectangle was drawn
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        if len(objects) > 0:
            rect_obj = objects[0]
            left = int(rect_obj["left"])
            top = int(rect_obj["top"])
            width = int(rect_obj["width"])
            height = int(rect_obj["height"])

            # Draw rectangle for visualization
            rect_image = image_np.copy()
            cv2.rectangle(rect_image, (left, top), (left + width, top + height), (0, 255, 0), 2)
            st.image(rect_image, caption="Selected Region", use_column_width=True)

            # Button to apply GrabCut
            if st.button("Remove Background"):
                with st.spinner("Processing..."):
                    rect = (left, top, width, height)
                    result_image = apply_grabcut(image_np, rect)

                    # Convert to Image format for display
                    result_image_pil = Image.fromarray(result_image)
                    st.image(result_image_pil, caption="Image with Background Removed", use_column_width=True)