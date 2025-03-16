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

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK',
        'message': 'Pandoc Conversion API',
        'endpoints': {
            '/': 'GET - Health check (this message)',
            '/convert': 'POST - Convert Markdown to DOCX'
        }
    })

@app.route('/convert', methods=['POST'])
def convert():
    logger.info('Received conversion request')
    
    # Kiểm tra Pandoc
    try:
        pandoc_version = subprocess.check_output(['pandoc', '--version'], text=True)
        logger.info(f"Pandoc version: {pandoc_version.splitlines()[0]}")
    except Exception as e:
        logger.error(f"Error checking pandoc: {e}")
        return jsonify({'error': f'Pandoc not available: {str(e)}'}), 500
    
    data = request.get_json()
    if not data or 'markdown' not in data:
        logger.error('No markdown provided in request')
        return jsonify({'error': 'No markdown provided'}), 400
        
    markdown_content = data['markdown']
    md_file_path = None
    output_docx_path = None
    
    try:
        # Tạo file Markdown tạm thời
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, dir=TEMP_DIR) as md_file:
            md_file.write(markdown_content)
            md_file_path = md_file.name
        
        # Tạo tên file docx đầu ra
        output_docx = tempfile.NamedTemporaryFile(suffix='.docx', delete=False, dir=TEMP_DIR)
        output_docx_path = output_docx.name
        output_docx.close()
        
        # Chuẩn bị lệnh Pandoc
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
        
        # Ghi log lệnh đang thực thi
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Chạy lệnh và bắt cả output để debug
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Pandoc error: {stderr}")
            return jsonify({'error': f'Pandoc conversion failed: {stderr}'}), 500
        
        logger.info('Pandoc conversion successful')
        
        # Kiểm tra file có tồn tại không
        if not os.path.exists(output_docx_path):
            logger.error(f"Output file not created at {output_docx_path}")
            return jsonify({'error': 'Output file was not created'}), 500
        
        # Lưu trữ đường dẫn file output để xóa sau khi gửi response
        response_file_path = output_docx_path
        
        return send_file(
            response_file_path,
            as_attachment=True,
            download_name='document.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Xóa file tạm - chỉ nếu chúng tồn tại và không đang được sử dụng
        # Lưu ý: Flask sẽ xử lý file khi gửi response và đóng nó sau đó
        # Nên không cần thiết xóa file output ngay lập tức
        if md_file_path and os.path.exists(md_file_path):
            try:
                os.remove(md_file_path)
                logger.debug(f"Removed temp markdown file: {md_file_path}")
            except Exception as e:
                logger.debug(f"Error removing markdown file: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
