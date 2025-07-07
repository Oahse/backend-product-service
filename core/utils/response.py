from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

def get_message_from_code(code: int) -> str:
    """
    Get the message based on the HTTP status code.

    Parameters:
    - code: The HTTP status code.

    Returns:
    - str: The corresponding message.
    """
    message_dict = {
        # Informational responses (100–199)
        100: "Continue",
        101: "Switching Protocols",
        102: "Processing (WebDAV)",
        103: "Early Hints",

        # Successful responses (200–299)
        200: "Request processed successfully",
        201: "Created",
        202: "Accepted",
        203: "Non-Authoritative Information",
        204: "No Content",
        205: "Reset Content",
        206: "Partial Content",
        207: "Multi-Status (WebDAV)",
        208: "Already Reported (WebDAV)",
        226: "IM Used",

        # Redirection responses (300–399)
        300: "Multiple Choices",
        301: "Moved Permanently",
        302: "Found",
        303: "See Other",
        304: "Not Modified",
        305: "Use Proxy",
        306: "Switch Proxy",
        307: "Temporary Redirect",
        308: "Permanent Redirect",

        # Client error responses (400–499)
        400: "Bad Request",
        401: "Unauthorized",
        402: "Payment Required",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        406: "Not Acceptable",
        407: "Proxy Authentication Required",
        408: "Request Timeout",
        409: "Conflict",
        410: "Gone",
        411: "Length Required",
        412: "Precondition Failed",
        413: "Payload Too Large",
        414: "URI Too Long",
        415: "Unsupported Media Type",
        416: "Range Not Satisfiable",
        417: "Expectation Failed",
        418: "I'm a teapot (RFC 2324)",
        421: "Misdirected Request",
        422: "Unprocessable Entity (WebDAV)",
        423: "Locked (WebDAV)",
        424: "Failed Dependency (WebDAV)",
        425: "Too Early",
        426: "Upgrade Required",
        428: "Precondition Required",
        429: "Too Many Requests",
        431: "Request Header Fields Too Large",
        451: "Unavailable For Legal Reasons",

        # Server error responses (500–599)
        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
        505: "HTTP Version Not Supported",
        506: "Variant Also Negotiates",
        507: "Insufficient Storage (WebDAV)",
        508: "Loop Detected (WebDAV)",
        510: "Not Extended",
        511: "Network Authentication Required",
    }

    # Default to the status code if not found in the dictionary
    return message_dict.get(code, f"Unknown status code {code}")

def Response(data=None, success=True, message=None, code=200):
    """
    A generic response handler for JSON responses with status, message, and data.

    Parameters:
    - data: The actual data to return (default is None).
    - status: The status of the response, typically 'success' or 'error' (default is 'success').
    - message: A message describing the response (default is 'Request processed successfully').
    - code: The HTTP status code to return (default is 200).

    Returns:
    - JSONResponse: A JSON response with the provided data, status, message, and status code.
    """
    # Use provided message or default to the one based on the code
    r_message = message if message else get_message_from_code(code)
    
    return JSONResponse(
        content={
            "data": data,
            "message": r_message,
            "success": success
        },
        status_code=code
    )
