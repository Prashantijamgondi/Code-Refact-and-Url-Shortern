from flask import Flask, request, jsonify, g
from functools import wraps
import sqlite3
import logging
import secrets
import hashlib
import re
from datetime import datetime
import os
import json

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY']=secrets.token_hex(32)

DATABASE='users.db'

def get_db():
    if('db' not in g):
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db=g.pop('db', None)
    if db is not None:
        db.close()

def validate_email(email):
    if(not email or len(email) >254):
        return False
    pattern =r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_name(name):
    if not name or not isinstance(name, str):
        return False
    return 1<=len(name.strip())<=100

def validate_password(password):
    if(not password or not isinstance(password, str)):
        return False
    return len(password)>=6

def hash_password(password):
    salt=secrets.token_hex(16)
    password_hash=hashlib.sha256((password+salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"    
    
def verify_password(password, stored_hash):
    try:
        salt,password_hash=stored_hash.split(':')
        return hashlib.sha256((password+salt).encode()).hexdigest()==password_hash
    except ValueError:
        return False

def validate_user_id(user_id):
    try:
        uid=int(user_id)
        return uid > 0
    except ValueError:
        return False
    
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return jsonify({"error": "Database error occurred"}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return jsonify({"error": "Internal server error"}), 500
    return decorated_function

@app.route('/', methods=['GET'])
def home():
    return "User Management System"

@app.route('/users', methods=['GET'])
@handle_errors
def get_all_users():
    db=get_db()
    cursor=db.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id")
    users = cursor.fetchall()
    
    users_list=[dict(user) for user in users]
    return jsonify({
        "users": users_list,
        "count": len(users_list)
    })

@app.route('/user/<user_id>', methods=['GET'])
@handle_errors
def get_user(user_id):
    if not validate_user_id(user_id):
        return jsonify({"error": "Invalid user ID"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id= ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        return jsonify({"user": dict(user)})
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/users', methods=['POST'])
@handle_errors
def create_user():
    if(not request.is_json):
        return jsonify({"error":"Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([name, email, password]):
        return jsonify({"error": "Missing required fields: name, passowrd and email"}), 400
    
    if not validate_name(name):
        return jsonify({"error": "Invalid name (1-100 characters required)"}), 400
    
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    if not validate_password(password):
        return jsonify({"error":"Pasword must be at least 6 characters"}), 400
    
    password_hash = hash_password(password)
    
    db=get_db()
    cursor=db.cursor()
    
    try:
        cursor.execute('INSERT INTO users(name, email, passowrd) VALUES(?,?,?)',
        (name.strip(), email.strip(), password_hash))
        db.commit()
        user_id=cursor.lastrowid
        
        logger.info(f"User created with ID: {user_id}")
        return jsonify({
            "message": "user Created Successfully",
            "user_id": user_id
        }), 201

    except sqlite3.IntegrityError as e:
        if "email" in str(e):
            return jsonify({"error": "Email Already Exists"}), 409
        else:
            return jsonify({"error":"User creation Failed"}), 409       


@app.route('/user/<user_id>', methods=['PUT'])
@handle_errors
def update_user(user_id):
    if(not validate_user_id(user_id)):
        return jsonify({"error": "Invalid user ID"}), 400
    
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400    
    
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    name = data.get('name')
    email = data.get('email')
    
    if(not name and not email):
        return jsonify({"error":"At least 1 field(name or email) is required"}), 400
    
    if name and not validate_name(name):
        return jsonify({"error": "Invalid name (1-100 characters required)"}), 400
    
    if email and not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    db=get_db()
    cursor=db.cursor()
    
    cursor.execute("SELECT id from users WHERE id=?", (user_id))
    if not cursor.fetchone():
        return jsonify({"error":"User Not Found"}), 404
    
    update_field = []
    params=[]
    if name:
        update_field.append("name = ?")
        params.append(name.strip())
    
    if email:
        update_field.append("email = ?")
        params.append(email.strip())
        
    params.append(user_id)
    
    try:
        cursor.execute(
            f"UPDATE users SET {', '.join(update_field)} WHERE id=?",params
        )
        db.commit()
        
        logger.info(f"User {user_id} updated Successfully")
        return jsonify({"message": "User updated successfully"}), 200
    
    except sqlite3.InternalError as e:
        if("email" in str(e)):
            return jsonify({"error": "Email already exists"}), 409
        else:
            return jsonify({"error": "Update Failed"}), 409


@app.route('/user/<user_id>', methods=['DELETE'])
@handle_errors
def delete_user(user_id):
    if not validate_user_id(user_id):
        return jsonify({"error": "Invalid user Id"}), 400
    
    db=get_db()
    cursor=db.cursor()
    
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    
    if(cursor.rowcount>0):
        logger.info(f"user {user_id} deleted")
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        return jsonify({"error": "User not found"}), 404


@app.route('/search', methods=['GET'])
@handle_errors
def search_users():
    name = request.args.get('name')
    
    if not name or len(name.strip())<1:
        return jsonify({"error":"Please provide a name to search(min 1 char required)"}), 400
    
    if len(name) > 100:
        return jsonify({"error": "Search term too long (maximum 100 characters)"}), 400

    db = get_db()
    cursor = db.cursor()
    search_term=f"%{name.strip()}%"
    cursor.execute(f"SELECT * FROM users WHERE name LIKE ? ORDER BY id", (search_term,))
    users = cursor.fetchall()
    
    users_list=[dict(user) for user in users]
    return jsonify({
        "users": users_list,
        "count": len(users_list),
        "search_term": name.strip()
    })


@app.route('/login', methods=['POST'])
@handle_errors
def login():
    if(not request.is_json):
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    email = data.get('email')
    password = data.get('password')
    
    if(not email or not password):
        return jsonify({"error": "Email and password are required"}), 400
    
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    db=get_db()
    cursor=db.cursor()

    cursor.execute(f"SELECT * FROM users WHERE email = ?", (email.lower(),))
    user = cursor.fetchone()
    
    if user and verify_password(password, user['password']):
        logger.info(f"Successful login for user: {user['id']}")
        return jsonify({
            "status": "success", 
            "user_id": user[0],
            "name": user['name']
        })
    else:
        logger.warning(f"Failed login attempt for email: {email}")
        return jsonify({
            "status": "failed",
            "error": "Invalid Credentials"
        }), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not Found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method Not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server Error"}), 500


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='127.0.0.1', port=5000, debug=debug_mode)
