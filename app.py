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

# Halaman Create Admin dan User
@app.route('/user')
@login_required
@role_required('admin')
def user():
    users = list(db.users.find())
    return render_template('admin/user/user.html', users=users, current_route=request.path)

@app.route('/addUser', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def addUser():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        hashed_password = generate_password_hash(password)

        user_document = {
            '_id': username,
            'username': username,
            'password': hashed_password,
            'role': role
        }

        try:
            db.users.insert_one(user_document)
        except:
            flash('Username already exists')
            return redirect(url_for('user'))

        return redirect(url_for('user'))
    return render_template('admin/user/addUser.html')

@app.route('/editUser/<_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editUser(_id):
    user = db.users.find_one({"_id": _id})
    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        password = request.form['password']

        update_fields = {
            'username': username,
            'role': role
        }

        if password:
            hashed_password = generate_password_hash(password)
            update_fields['password'] = hashed_password
            update_fields['password_length'] = len(password)  # Store the length of the new password

        try:
            db.users.update_one({"_id": _id}, {"$set": update_fields})
            flash("User updated successfully")
        except Exception as e:
            flash(f"An error occurred: {e}")

        return redirect(url_for('user'))

    return render_template('admin/user/editUser.html', user=user)

@app.route('/deleteUser/<_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def deleteUser(_id):
    db.users.delete_one({"_id": _id})
    return redirect(url_for("user"))



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


# Halaman logout
@app.route('/logoutAdmin')
def logout():
    session.clear()
    return redirect(url_for('loginAdmin'))

@app.route('/')
def home():
    return render_template('page/home.html')

@app.route('/pageProduct')
@login_required
@role_required('user')
def pageProduct():
    return render_template('page/product.html')

@app.route('/detail')
@login_required
@role_required('user')
def detail():
    return render_template('page/detail.html')

@app.route('/about')
def about():
    return render_template('page/about.html')

@app.route('/contact')
def contact():
    return render_template('page/kontak.html')

# Halaman Dashboard
@app.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    return render_template('admin/dashboard.html', current_route=request.path)

# Produk ###############################################################################################
# Halaman Produk ###############################################################################################
@app.route('/product')
@login_required
@role_required('admin')
def product():
    products = list(db.products.find())
    return render_template('admin/product/product.html', products=products, current_route=request.path)

@app.route('/addProduct', methods=['GET','POST'])
@login_required
@role_required('admin')
def addProduct():
    product_exists = False

    if request.method=='POST':
        nama = request.form['nama']
        satuan = request.form['satuan']
        harga = request.form['harga']
        deskripsi = request.form['deskripsi']
        nama_gambar = request.files['gambar']
        stok = int(request.form.get('stok', 0))

        # Periksa apakah Nama Barang dengan nama yang sama sudah ada
        existing_product = db.products.find_one({'nama': nama})
        if existing_product:
            product_exists = True
        else:
            if nama_gambar:
                nama_file_asli = nama_gambar.filename
                nama_file_gambar = nama_file_asli.split('/')[-1]
                file_path = f'static/assets/imgProducts/{nama_file_gambar}'
                nama_gambar.save(file_path)
            else:
                nama_file_gambar = None
            
            doc = {
                'nama':nama,
                'gambar': nama_file_gambar,
                'satuan': satuan,
                'harga': harga,
                'deskripsi': deskripsi,
                'stok': stok
            }
            db.products.insert_one(doc)
            return redirect(url_for("product"))

    return render_template('admin/product/addProduct.html', product_exists=product_exists)

@app.route('/editProduct/<_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editProduct(_id):
    product_exists = False

    if request.method == 'POST':
        id = request.form['_id']  
        nama = request.form['nama']
        satuan = request.form['satuan']
        harga = request.form['harga']
        deskripsi = request.form['deskripsi']
        nama_gambar = request.files['gambar']
        stok = int(request.form.get('stok', 0))

        # Periksa apakah Nama Barang dengan nama yang sama sudah ada
        existing_product = db.products.find_one({'nama': nama, '_id': {'$ne': ObjectId(id)}})
        if existing_product:
            product_exists = True
        else:
            doc = {
                'nama': nama,
                'satuan': satuan,
                'harga': harga,
                'deskripsi': deskripsi
            }
            if nama_gambar:
                nama_file_asli = nama_gambar.filename
                nama_file_gambar = nama_file_asli.split('/')[-1]
                file_path = f'static/assets/imgProducts/{nama_file_gambar}'
                nama_gambar.save(file_path)
                doc['gambar'] = nama_file_gambar

            db.products.update_one({"_id": ObjectId(id)}, {"$set": doc}) 
            return redirect(url_for("product"))

    id = ObjectId(_id)
    data = list(db.products.find({"_id": id}))
    return render_template('admin/product/editProduct.html', data=data, product_exists=product_exists)


@app.route('/deleteProduct/<_id>', methods=['GET','POST'])
@login_required
@role_required('admin')
def deleteProduct(_id):
    _id = ObjectId(_id)
    db.products.delete_one({"_id": ObjectId(_id)})
    return redirect(url_for("product"))

# Supplier ###############################################################################################
# Halaman Suplier ###############################################################################################
@app.route('/supplier')
@login_required
@role_required('admin')
def supplier():
    suppliers = list(db.suppliers.find())
    return render_template('admin/supplier/supplier.html', suppliers=suppliers, current_route=request.path)

@app.route('/addSupplier', methods=['GET','POST'])
@login_required
@role_required('admin')
def addSupplier():
    supplier_exists = False

    if request.method=='POST':
        nama = request.form['nama']
        alamat = request.form['alamat']
        noTelp = request.form['noTelp']
        nama_gambar = request.files['gambar']

        # Periksa apakah Nama Barang dengan nama yang sama sudah ada
        existing_supplier = db.suppliers.find_one({'nama': nama})
        if existing_supplier:
            supplier_exists = True
        else:
            if nama_gambar:
                nama_file_asli = nama_gambar.filename
                nama_file_gambar = nama_file_asli.split('/')[-1]
                file_path = f'static/assets/imgSuppliers/{nama_file_gambar}'
                nama_gambar.save(file_path)
            else:
                nama_file_gambar = None
            
            doc = {
                'nama':nama,
                'alamat':alamat,
                'gambar': nama_file_gambar,
                'noTelp': noTelp,
            }
            db.suppliers.insert_one(doc)
            return redirect(url_for("supplier"))

    return render_template('admin/supplier/addSupplier.html', supplier_exists=supplier_exists)

@app.route('/editSupplier/<_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editSupplier(_id):
    supplier_exists = False

    if request.method == 'POST':
        id = request.form['_id']  
        nama = request.form['nama']
        alamat = request.form['alamat']
        noTelp = request.form['noTelp']
        nama_gambar = request.files['gambar']

        # Periksa apakah Nama Supplier dengan nama yang sama sudah ada
        existing_supplier = db.suppliers.find_one({'nama': nama, '_id': {'$ne': ObjectId(id)}})
        if existing_supplier:
            supplier_exists = True
        else:
            doc = {
                'nama': nama,
                'alamat': alamat,
                'noTelp': noTelp,
            }
            if nama_gambar:
                nama_file_asli = nama_gambar.filename
                nama_file_gambar = nama_file_asli.split('/')[-1]
                file_path = f'static/assets/imgSuppliers/{nama_file_gambar}'
                nama_gambar.save(file_path)
                doc['gambar'] = nama_file_gambar

            db.suppliers.update_one({"_id": ObjectId(id)}, {"$set": doc}) 
            return redirect(url_for("supplier"))

    id = ObjectId(_id)
    data = list(db.suppliers.find({"_id": id}))
    return render_template('admin/supplier/editSupplier.html', data=data, supplier_exists=supplier_exists)

@app.route('/deleteSupplier/<_id>', methods=['GET','POST'])
@login_required
@role_required('admin')
def deleteSupplier(_id):
    _id = ObjectId(_id)
    db.suppliers.delete_one({"_id": ObjectId(_id)})
    return redirect(url_for("supplier"))

# Stock ###############################################################################################
# Halaman Stock ###############################################################################################
@app.route('/stock')
@login_required
@role_required('admin')
def stock():
    products = list(db.products.find())
    return render_template('admin/stock/stock.html', products=products, current_route=request.path)

def get_supplier_name(supplier_id):
    supplier = db.suppliers.find_one({'_id': ObjectId(supplier_id)})
    if supplier:
        return supplier['nama']
    else:
        return None

@app.route('/editStock/<_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def editStock(_id):
    if request.method == 'POST':
        id = ObjectId(_id)
        pengurangan = int(request.form['pengurangan'])
        keterangan = request.form['keterangan']

        # Simpan informasi pengurangan stok dan keterangan (jika ada) ke dalam tabel lain
        if pengurangan > 0:
            pengurangan_doc = {
                'nama_barang': db.products.find_one({'_id': id})['nama'],
                'jumlah_pengurangan': pengurangan,
                'keterangan': keterangan
            }
            db.pengurangan.insert_one(pengurangan_doc)

            # Kurangi stok di koleksi 'products'
            db.products.update_one(
                {'_id': id},
                {'$inc': {'stok': -pengurangan}}
            )

        return redirect(url_for('stock'))

    # Jika metode adalah GET, tampilkan halaman editStock.html dengan data produk yang sesuai
    id = ObjectId(_id)
    product = db.products.find_one({'_id': id})
    return render_template('admin/stock/editStock.html', product=product)


# pembelian ###############################################################################################
# Halaman pembelian ###############################################################################################
@app.route('/pembelian')
@login_required
@role_required('admin')
def pembelian():
    suppliers = list(db.suppliers.find())
    products = list(db.products.find())

    purchase_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    current_date = datetime.now().strftime("%d-%m-%Y")

    return render_template('admin/pembelian/pembelian.html', products=products, suppliers=suppliers, current_route=request.path, purchase_code=purchase_code, current_date=current_date)

@app.route('/supplier/<supplier_id>')
@login_required
@role_required('admin')
def get_supplier(supplier_id):
    supplier = db.suppliers.find_one({'_id': ObjectId(supplier_id)})
    if supplier:
        supplier['_id'] = str(supplier['_id'])
        return jsonify(supplier)
    else:
        return jsonify({'error': 'Supplier not found'}), 404

@app.route('/product/<product_id>')
@login_required
@role_required('admin')
def get_product(product_id):
    product = db.products.find_one({'_id': ObjectId(product_id)})
    if product:
        product['_id'] = str(product['_id'])
        return jsonify(product)
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/addPembelian', methods=['POST'])
def addPembelian():
    try:
        data = request.json
        pembelian = data.get('pembelian', [])

        for pembelian_item in pembelian:
            # Convert the date string to datetime object and then format it
            pembelian_item['tanggal_pembelian'] = datetime.strptime(pembelian_item['tanggal_pembelian'], '%Y-%m-%d').strftime('%d-%m-%Y')
            for item in pembelian_item['items']:
                item['harga'] = int(item['harga'])
                item['jumlah'] = int(item['jumlah'])
                item['total_harga'] = int(item['total_harga'])

                # Ensure 'satuan' is included in the item
                if 'satuan' not in item:
                    product_id = item['_id']
                    product = db.products.find_one({"_id": ObjectId(product_id)})
                    if product:
                        item['satuan'] = product.get('satuan', 'undefined')

                # Update the stock in the product collection
                product_id = item['_id']
                product = db.products.find_one({"_id": ObjectId(product_id)})
                if product:
                    new_stock = product['stok'] + item['jumlah']
                    db.products.update_one(
                        {"_id": ObjectId(product_id)},
                        {"$set": {"stok": new_stock}}
                    )

        db.purchases.insert_many(pembelian)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500






















if __name__ == '__main__':
    app.run(debug=True)
