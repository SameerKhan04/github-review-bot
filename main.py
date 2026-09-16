from dotenv import load_dotenv

load_dotenv()

import app.logging_setup  # noqa: E402,F401
from app.api import app  # noqa: E402
from app.database import init_db  # noqa: E402

init_db()

if __name__ == "__main__":
    import os

    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=debug)
