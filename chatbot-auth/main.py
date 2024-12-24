from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import psycopg2
import bcrypt
import os

# Initialize Flask app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'chatbot_jwt_secret_key'
jwt = JWTManager(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["5 per second"],
    storage_uri="memory://",
)

CORS(app, resources={r"/*": {"origins": "*"}})

# Database connection details
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysecretpassword")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ice")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
    )

@app.route('/login', methods=['POST'])
@limiter.limit("5 per second")
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve user information
        query = """
        SELECT u.user_id as uid, r.role_id, d.name as department, d.key as department_key, u.gender, uc.password_hash
        FROM user_credentials uc
        JOIN users u ON uc.user_id = u.user_id
        JOIN departments d ON u.department_id = d.id
		JOIN roles r ON r.role_id = u.role_id
        WHERE u.email = %s;
        """
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Invalid email or password."}), 401

        uid, role_id, department, department_key, gender, password_hash = user

        # Verify password
        print(password)
        if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            return jsonify({"error": "Invalid email or password."}), 401

        # Create JWT token
        access_token = create_access_token(
            identity={
                "uid": uid,
                "role_id": role_id,
                "department": department,
                "department_key": department_key,
                "gender": gender,
                "authenticated": True
            }
        )
        if conn:
            cursor.close()
            conn.close()
        return jsonify({"access_token": access_token}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
