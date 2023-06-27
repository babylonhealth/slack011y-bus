from flask import jsonify


def bad_request(error):
    return jsonify({"error": error.description}), 400


def resource_not_found(error):
    return jsonify({"error": error.description}), 404


def conflict(error):
    return jsonify({"error": error.description}), 409


def error_server(error):
    return jsonify({"error": error.description}), 500
