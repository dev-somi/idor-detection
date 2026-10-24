import os
from config import api_app
alive = int(os.getenv('tokentimetolive', 60))
if __name__ == '__main__':
    api_app.run(host='0.0.0.0', port=5000)
