from dotenv import load_dotenv

from app.api import app

# Load environment variables before the app starts
load_dotenv()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)