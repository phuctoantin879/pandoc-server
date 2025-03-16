from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import subprocess
import tempfile
import os
import shutil
import atexit
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

TEMP_DIR = tempfile.mkdtemp()

def cleanup():
    try:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        logger.info(f"Cleaned up temporary directory: {TEMP_DIR}")
    except Exception as e:
        logger.error(f"Error cleaning up temporary directory: {e}")

atexit.register(cleanup)

@app.route('/convert', methods=['POST'])
def convert():
    logger.info('Received conversion request')
    
    data = request.get_json()
    if not data or 'markdown' not in data:
        logger.error('No markdown provided in request')
        return jsonify({'error': 'No markdown provided'}), 400
        
    markdown_content = data['markdown']
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir=TEMP_DIR) as md_file:
            md_file.write(markdown_content)
            md_file_path = md_file.name
        
        output_docx = tempfile.NamedTemporaryFile(suffix='.docx', delete=False, dir=TEMP_DIR)
        output_docx_path = output_docx.name
        output_docx.close()
        
        cmd = [
            'pandoc',
            md_file_path,
            '-o', output_docx_path,
            '--from=markdown',
            '--to=docx',
            '--standalone',
            '--wrap=none',
            '--mathml'
        ]
        
        subprocess.check_call(cmd)
        logger.info('Pandoc conversion successful')
        
        return send_file(
            output_docx_path,
            as_attachment=True,
            download_name='document.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        return jsonify({'error': str(e)}), 500
        
    finally:
        try:
            os.remove(md_file_path)
            os.remove(output_docx_path)
        except:
            pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=False, host='0.0.0.0', port=port)
