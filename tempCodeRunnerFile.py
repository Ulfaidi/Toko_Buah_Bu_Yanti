@app.route('/checkUserName', methods=['POST'])
def check_user_name():
    data = request.json
    user_name = data.get('nama', '')
    
    existing_user = db.users.find_one({'nama': user_name})
    if existing_user:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})