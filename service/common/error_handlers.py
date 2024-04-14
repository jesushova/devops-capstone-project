from flask import jsonify
from service.models import DataValidationError
from service import app
from . import status

def handle_error(status_code, error_name, message):
    """Handles the creation of error responses"""
    app.logger.warning(message)
    response = jsonify(
        status=status_code,
        error=error_name,
        message=message,
    )
    response.status_code = status_code
    return response

@app.errorhandler(DataValidationError)
def handle_data_validation_error(error):
    """Handles DataValidationError"""
    return handle_error(
        status.HTTP_400_BAD_REQUEST, "Bad Request", str(error)
    )

@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def handle_bad_request(error=None):
    """Handles HTTP 400 Bad Request"""
    message = str(error) if error else "Bad Request"
    return handle_error(
        status.HTTP_400_BAD_REQUEST, "Bad Request", message
    )

@app.errorhandler(status.HTTP_404_NOT_FOUND)
def handle_not_found(error=None):
    """Handles HTTP 404 Not Found"""
    message = str(error) if error else "Not Found"
    return handle_error(
        status.HTTP_404_NOT_FOUND, "Not Found", message
    )

@app.errorhandler(status.HTTP_405_METHOD_NOT_ALLOWED)
def handle_method_not_supported(error=None):
    """Handles HTTP 405 Method Not Allowed"""
    message = str(error) if error else "Method not Allowed"
    return handle_error(
        status.HTTP_405_METHOD_NOT_ALLOWED, "Method not Allowed", message
    )

@app.errorhandler(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
def handle_media_type_not_supported(error=None):
    """Handles HTTP 415 Unsupported Media Type"""
    message = str(error) if error else "Unsupported media type"
    return handle_error(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported media type", message
    )

@app.errorhandler(status.HTTP_500_INTERNAL_SERVER_ERROR)
def handle_internal_server_error(error=None):
    """Handles HTTP 500 Internal Server Error"""
    message = str(error) if error else "Internal Server Error"
    app.logger.error(message)
    return handle_error(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", message
    )
