from flask import Flask

def create_app(point_set_client=None, triangulation_service=None):
    """
    Factory function to create the Flask application.
    Dependencies are injected for easier testing.
    """
    app = Flask(__name__)

    # TODO: Register blueprints or routes here
    # @app.route("/triangulation/<point_set_id>") ...

    return app