import os

# PUBLIC_INTERFACE
def create_app():
    """WSGI entrypoint for Gunicorn to load the Flask application.

    Returns:
        Flask: The configured Flask app created by app.create_app().
    """
    # Import inside function to avoid side effects at module import and to
    # prevent confusion with the package named 'app/'.
    from app import create_app as factory  # this refers to app.py module
    return factory()

if __name__ == "__main__":
    # Allow running directly for local dev
    app = create_app()
    port = int(os.getenv("PORT", "3001"))
    app.run(host="0.0.0.0", port=port)
