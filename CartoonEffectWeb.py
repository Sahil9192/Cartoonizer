from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
import cv2
import numpy as np
import os
import time
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# Ensure the "uploads" folder exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('CartoonEffectHTML.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return "No image uploaded", 400

    file = request.files['image']
    if file.filename == '':
        return "No selected file", 400

    # Save the uploaded file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Generate favicon.ico
    create_favicon(file_path)

    return "Favicon created and set!"

def create_favicon(image_path):
    # Use Pillow to resize the image
    with Image.open(image_path) as img:
        img = img.resize((16, 16))  # Resize to 16x16 pixels
        favicon_path = os.path.join(app.config['UPLOAD_FOLDER'], 'favicon.ico')
        img.save(favicon_path, format='ICO')

# Route to serve the dynamically created favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.config['UPLOAD_FOLDER'], 'favicon.ico')

# Resize the image for faster processing
def resize_image(img, max_width=800, max_height=800):
    height, width = img.shape[:2]
    if width > max_width or height > max_height:
        scale = min(max_width / width, max_height / height)
        new_size = (int(width * scale), int(height * scale))
        img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
    return img

# Edge detection
def edge_marks(img, line_size, blur_value):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray_blur = cv2.medianBlur(gray, blur_value)
    edges = cv2.adaptiveThreshold(
        gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, line_size, blur_value
    )
    return edges

# Color quantization
def color_quantization(img, k):
    data = np.float32(img).reshape((-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.001)
    ret, label, center = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center = np.uint8(center)
    result = center[label.flatten()]
    result = result.reshape(img.shape)
    return result

# Cartoonize the image
def cartoonize_image(img, line_size=5, blur_value=5, k=6):
    edges = edge_marks(img, line_size, blur_value)
    quantized_img = color_quantization(img, k)
    blurred = cv2.bilateralFilter(quantized_img, d=9, sigmaColor=100, sigmaSpace=100)
    cartoon = cv2.bitwise_and(blurred, blurred, mask=edges)
    return cartoon

@app.route('/process', methods=['POST'])
def process_image():
    try:
        # Get the uploaded file
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save the uploaded file to the "uploads" folder
        filename = f"{int(time.time())}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Read the image
        img = cv2.imread(filepath)
        if img is None:
            return jsonify({'error': 'Invalid image file'}), 400

        # Convert and resize the image
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = resize_image(img)

        # Process the image into a cartoon
        line_size = int(request.form.get('line_size', 5))
        blur_value = int(request.form.get('blur_value', 5))
        num_colors = int(request.form.get('num_colors', 6))
        cartoon = cartoonize_image(img, line_size, blur_value, num_colors)

        # Convert the cartoonized image to bytes
        _, img_encoded = cv2.imencode('.jpg', cv2.cvtColor(cartoon, cv2.COLOR_RGB2BGR))
        img_io = BytesIO(img_encoded.tobytes())

        return send_file(img_io, mimetype='image/jpeg')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
