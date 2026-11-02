"""TruthLens Flask application.  Run:  python backend/app.py   (from the project root)"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # make `config`, `services`, ... importable

from flask import Flask
from flask_cors import CORS

from config import Config
from database.mongo import MongoStore
from utils.responses import ApiError, fail
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({
        "message": "TruthLens API is running!"
    })

@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy"
    })

if __name__ == "__main__":
    app.run(debug=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("truthlens")


def create_app(store=None):
    app = Flask(__name__)
    app.config["STORE"] = store if store is not None else MongoStore(Config.MONGO_URI, Config.MONGO_DB_NAME)
    CORS(app, origins=Config.CORS_ORIGINS)

    from routes.api import bp
    app.register_blueprint(bp)

    @app.errorhandler(ApiError)
    def _api_error(e):
        return fail(e.message, e.status, e.code)

    @app.errorhandler(404)
    def _404(_):
        return fail("Endpoint not found.", 404, "NOT_FOUND")

    @app.errorhandler(405)
    def _405(_):
        return fail("Method not allowed.", 405, "METHOD_NOT_ALLOWED")

    @app.errorhandler(Exception)
    def _unhandled(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return fail(e.description, e.code or 500)
        log.exception("Unhandled error")
        return fail("Unexpected server error. Check the backend log.", 500, "INTERNAL_ERROR")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=Config.PORT, debug=Config.ENV == "development")
