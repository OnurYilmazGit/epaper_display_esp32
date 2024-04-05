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

    # Extract the array data
    array_data_str = content.split('{', 1)[1].split('}', 1)[0]
    array_data = [int(x, 16) for x in array_data_str.split(',') if x.strip().startswith('0X')]

    # Write to a .bin file
    with open(output_file, 'wb') as bin_file:
        bin_file.write(bytearray(array_data))

@app.route('/process-image', methods=['POST'])
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
    esp32_upload_url = 'http://172.20.10.2/upload'
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

if __name__ == '__main__':
    app.run(debug=True)
