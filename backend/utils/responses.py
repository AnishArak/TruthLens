"""Structured JSON helpers so every endpoint answers in the same shape."""
from flask import jsonify


def ok(data=None, status=200, **extra):
    body = {"success": True, "data": data}
    body.update(extra)
    return jsonify(body), status


def fail(message, status=400, code=None, **extra):
    body = {"success": False, "error": {"message": message, "code": code or f"HTTP_{status}"}}
    body.update(extra)
    return jsonify(body), status


class ApiError(Exception):
    """Raise inside services/routes to return a clean JSON error."""

    def __init__(self, message, status=400, code=None):
        super().__init__(message)
        self.message, self.status, self.code = message, status, code
