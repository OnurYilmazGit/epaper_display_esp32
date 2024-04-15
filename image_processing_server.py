from flask import Flask, request, jsonify
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os
from datetime import datetime
import requests 

app = Flask(__name__)

def convert_h_to_bin(input_file, output_file):
    # Read the .h file content
    with open(input_file, 'r') as file:
        content = file.read()

    array_data_str = content.split('{', 1)[1].split('}', 1)[0]
    array_data = [int(x, 16) for x in array_data_str.split(',') if x.strip().startswith('0X')]

    # Write to a .bin file
    with open(output_file, 'wb') as bin_file:
        bin_file.write(bytearray(array_data))

esp32_base_url = 'http://192.168.0.119'

@app.route('/clear', methods=['GET'])
def clear_display():
    try:
        response = requests.get('http://192.168.0.119/clear')
        return jsonify({'status': 'Successs', 'message': 'Clear command sent to ESP32.'})
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 500

@app.route('/cross', methods=['GET'])
def epaper_cross():
    response = requests.get(f'{esp32_base_url}/cross')
    return jsonify({'status': 'cross called', 'esp32_response': response.text}), 200

@app.route('/displayText', methods=['POST'])
def send_text_to_display():
    text_content = request.json.get('text')
    if not text_content:
        return jsonify({'error': 'No text provided'}), 400

    # Prepare the form data payload for the ESP32
    payload = {'plain': text_content}

    try:
        response = requests.post(f'{esp32_base_url}/displayText', data=payload)
        return jsonify({'status': 'Sent to ESP32', 'ESP32_response': response.text}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Failed to connect to ESP32', 'message': str(e)}), 500


@app.route('/displayImage', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return "No image provided", 400

    file = request.files['image']

    # Process the image
    image = Image.open(file.stream)
    contrast_enhancer = ImageEnhance.Contrast(image)
    image = contrast_enhancer.enhance(2.0)
    image = image.filter(ImageFilter.SHARPEN)
    image = image.resize((200, 200))
    image = image.convert('1')

    # Generate a unique filename for saving
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'processed_{timestamp}.jpg'
    c_array_filename = f'IMG_0001.h'
    bin_filename = f'IMG_0001.bin'

    image.save(filename)

    # Convert the image to a C array
    image_array = np.array(image).astype(np.uint8)
    packed_image = np.packbits(image_array.flatten())
    hex_values = ['0X{:02X}'.format(byte) for byte in packed_image]
    output_width = 16
    hex_array_str = ',\n'.join(', '.join(hex_values[i:i+output_width]) for i in range(0, len(hex_values), output_width))
    c_array = f'const unsigned char IMAGE_BLACK[] PROGMEM = {{\n{hex_array_str}\n}};'

    # Save the C array to a file
    with open(c_array_filename, 'w') as f:
        f.write(c_array)

    # Convert the .h file to a .bin file
    convert_h_to_bin(c_array_filename, bin_filename)

    # Automatically upload the .bin file to the ESP32
    esp32_upload_url = 'http://192.168.0.119/upload'
    files = {'file': open(bin_filename, 'rb')}
    response = requests.post(esp32_upload_url, files=files)
    
    if response.status_code == 200:
        print("Upload to ESP32 successful")
    else:
        print("Failed to upload to ESP32. Status code:", response.status_code)
    

    return jsonify({
        'message': 'Image processed successfully',
        'image_path': filename,
        'c_array_path': c_array_filename,
        'bin_path': bin_filename
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)
