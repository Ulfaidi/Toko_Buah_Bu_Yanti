from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from bson.objectid import ObjectId
import random
import string

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Konfigurasi MongoDB
client = MongoClient('mongodb://tes:sparta@ac-3yctn6n-shard-00-00.tlo2vsi.mongodb.net:27017,ac-3yctn6n-shard-00-01.tlo2vsi.mongodb.net:27017,ac-3yctn6n-shard-00-02.tlo2vsi.mongodb.net:27017/?ssl=true&replicaSet=atlas-eeaf5d-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0')
db = client['inventory_db']

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or (session['role'] != role and session['role'] != 'admin'):
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('page/login.html')

# Halaman loginAdmin
@app.route('/loginAdmin', methods=['GET', 'POST'])
def loginAdmin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('admin/login.html')


# Halaman register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template('admin/register.html', registration_failed=True, error_message="Password Tidak Benar.")
        
        existing_user = db.users.find_one({'username': username})
        if existing_user:
            flash("Username already exists.")
            return render_template('admin/register.html', registration_failed=True, error_message="Username Sudah Ada.")
        
        hashed_password = generate_password_hash(password)
        user_document = {
            '_id': username,
            'username': username,
            'password': hashed_password,
            'role': 'user',
            'password_length': len(password)
        }
        
        try:
            db.users.insert_one(user_document)
            flash("Registration successful. Please log in.")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred: {e}")
            return render_template('admin/register.html', registration_failed=True, error_message=str(e))
    
    return render_template('admin/register.html')

# halaman produk buah
@app.route('/pageProduct')
@login_required
@role_required('user')
def pageProduct():
    return render_template('page/product.html')

# halaman detail buah
@app.route('/detail')
@login_required
@role_required('user')
def detail():
    return render_template('page/detail.html')

# halaman about (tentang kami)
@app.route('/about')
@login_required
@role_required('user')
def about():
    return render_template('page/about.html')

# halaman kontak
@app.route('/contact')
@login_required
@role_required('user')
def contact():
    return render_template('page/kontak.html')

# Halaman Dashboard
@app.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    return render_template('admin/dashboard.html', current_route=request.path)








if __name__ == '__main__':
    app.run(debug=True)
