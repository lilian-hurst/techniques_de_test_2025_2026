import uuid

from flask import Flask, jsonify, make_response

from . import algorithm, exceptions, serialization


def create_app(point_set_client=None, triangulation_service=None):
    app = Flask(__name__)
    algo_service = triangulation_service if triangulation_service else algorithm

    @app.route("/triangulation/<point_set_id>", methods=["GET"])
    def get_triangulation(point_set_id):
        try:
            val = uuid.UUID(point_set_id)
            if str(val) != point_set_id:
                raise ValueError("Non-canonical UUID")
        except ValueError:
            return jsonify({
                "code": "INVALID_POINT_SET_ID",
                "message": f"'{point_set_id}' is not a valid uuid"
            }), 400

        try:
            if not point_set_client:
                raise exceptions.PointSetManagerUnavailableError("Client unconfigured")

            point_set_bytes = point_set_client.fetch_point_set(point_set_id)
            result = algo_service.triangulate(point_set_bytes)

            if isinstance(result, bytes):
                response_payload = result
            else:
                points = serialization.bytes_to_point_set(point_set_bytes)
                response_payload = serialization.triangles_to_bytes(points, result)

            response = make_response(response_payload)
            response.headers["Content-Type"] = "application/octet-stream"
            return response, 200

        except exceptions.PointSetNotFoundError:
            return jsonify({"code": "POINT_SET_NOT_FOUND"}), 404

        except exceptions.PointSetManagerUnavailableError:
            return jsonify({"code": "POINT_SET_MANAGER_UNAVAILABLE"}), 502


        except (exceptions.TriangulatorError, exceptions.SerializationError, ValueError) as e:
            return jsonify({"code": "TRIANGULATION_FAILED", "message": str(e)}), 500


    return app



