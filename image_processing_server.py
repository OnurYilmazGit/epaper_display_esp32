from flask import Flask, request, jsonify
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os
from datetime import datetime
import requests 
import io

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

esp32_base_url = 'http://131.159.6.138:9023'

@app.route('/clear', methods=['GET'])
def clear_display():
    try:
        response = requests.get(f'{esp32_base_url}/clear', timeout=5)
        return jsonify({'status': 'Successs', 'message': 'Clear command sent to ESP32.'})
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'Error', 'message': str(e)}), 500

@app.route('/cross', methods=['GET'])
def epaper_cross():
    try:
        response = requests.get(f'{esp32_base_url}/cross', timeout=8)
    except requests.exceptions.RequestException as e:
        print('Failed to connect to ESP32:', str(e))
        return jsonify({'status': 'Error', 'message': str(e)}), 500

    return jsonify({'status': 'cross called', 'esp32_response': response.text}), 200

@app.route('/displayText', methods=['POST'])
def send_text_to_display():
    text_content = request.args.get('text')
    payload = {'plain': text_content}
    response = requests.get(f'{esp32_base_url}/displayText', timeout=5, data=payload)
    try:
        response = requests.post(f'{esp32_base_url}/displayText', data=payload)
        return jsonify({'status': 'Sent to ESP32', 'ESP32_response': response.text}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Failed to connect to ESP32', 'message': str(e)}), 500    

@app.before_request
def load_json():
    if request.method == 'POST':
        try:
            request.get_json(force=True)
        except Exception:
            pass

@app.route('/displayImage', methods=['POST'])
def process_image():
    data = request.get_json(silent=True)
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400

    image_url = data['url']
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Checks HTTP request for errors
        image = Image.open(io.BytesIO(response.content))
        if image.mode != 'RGB':
            image = image.convert('RGB')
    except requests.RequestException as e:
        return jsonify({'error': 'Error fetching image', 'message': str(e)}), 500
    except IOError as e:
        return jsonify({'error': 'Error opening image', 'message': str(e)}), 500

    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = image.filter(ImageFilter.SHARPEN)
    image = image.resize((200, 200), Image.LANCZOS)
    image = image.convert('1')  # Convert image to black and white

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'processed_{timestamp}.png'
    image.save(filename)

    image_array = np.array(image).astype(np.uint8)
    packed_image = np.packbits(image_array.flatten())
    hex_values = ['0X{:02X}'.format(byte) for byte in packed_image]
    hex_array_str = ',\n'.join(', '.join(hex_values[i:i+16]) for i in range(0, len(hex_values), 16))
    c_array = f'const unsigned char IMAGE_BLACK[] PROGMEM = {{\n{hex_array_str}\n}};'

    c_array_filename = f'IMG_0001.h'
    with open(c_array_filename, 'w') as f:
        f.write(c_array)

    bin_filename = f'IMG_0001.bin'
    convert_h_to_bin(c_array_filename, bin_filename)

    with open(bin_filename, 'rb') as bin_file:
        files = {'file': bin_file}
        try:
            esp32_response = requests.post('http://131.159.6.138:9023/upload', files=files)
            esp32_response.raise_for_status()
        except requests.RequestException as e:
            return jsonify({
                'error': 'Failed to upload to ESP32',
                'message': str(e),
                'status_code': esp32_response.status_code if esp32_response else 'No response'
            }), 500

    return jsonify({
        'message': 'Image processed and uploaded successfully',
        'paths': {
            'processed_image': filename,
            'c_array': c_array_filename,
            'binary_file': bin_filename
        },
        'esp32_response': esp32_response.text
    }), 200


@app.route('/downloadImage', methods=['POST'])
def download_image():
    # Log request headers and body for debugging
    print("Headers:", request.headers)
    print("Body:", request.data)
    print("Content-Type:", request.content_type)
    
    data = request.get_json(silent=True)
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided or the body is not JSON'}), 400

    image_url = data['url']
    try:
        response = requests.get(image_url)
        response.raise_for_status()

        filename = image_url.split('/')[-1]
        save_path = os.path.join('/home/mangler/Projects/epaper_display_esp32', filename)

        with open(save_path, 'wb') as f:
            f.write(response.content)

        return jsonify({'message': 'Image downloaded successfully', 'filename': filename}), 200

    except requests.HTTPError as http_err:
        return jsonify({'error': 'HTTP error occurred', 'details': str(http_err)}), 500
    except Exception as err:
        return jsonify({'error': 'An error occurred', 'details': str(err)}), 500


if __name__ == "__main__":
    app.run(host='::', port=5000, debug=True)
