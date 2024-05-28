from flask import Flask, request
import subprocess
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/run_scraper', methods=['POST'])
def run_scraper():
    script_name = request.json.get('script_name')
    if script_name:
        command = f'python {script_name}.py'
        logger.info(f'Starting scraper: {script_name}')
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            logger.info(f'Successfully ran {script_name}: {result.stdout}')
            return {'status': 'success', 'script': script_name}, 200
        except subprocess.CalledProcessError as e:
            logger.error(f'Error running {script_name}: {e.stderr}')
            return {'status': 'error', 'message': e.stderr}, 500
    else:
        return {'status': 'error', 'message': 'No script name provided'}, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
