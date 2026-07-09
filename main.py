from dotenv import load_dotenv

from app.api import app
from app.database import init_db

# Load environment variables before the app starts
load_dotenv()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)