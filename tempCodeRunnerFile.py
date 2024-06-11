@app.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    # Get current date and the date 7 days ago
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)  # We need a 7-day period including today

    # Fetch sales data for the last week
    sales_data = db.sale.find({
        'tanggal_penjualan': {
            '$gte': start_date.strftime('%d-%m-%Y'),
            '$lte': end_date.strftime('%d-%m-%Y')
        }
    })

    # Day name translation dictionary
    day_name_translation = {
        "Monday": "Senin",
        "Tuesday": "Selasa",
        "Wednesday": "Rabu",
        "Thursday": "Kamis",
        "Friday": "Jumat",
        "Saturday": "Sabtu",
        "Sunday": "Minggu"
    }
    
    # Initialize daily sales totals with Indonesian day names
    daily_sales = {day: 0 for day in day_name_translation.values()}

    # Process sales data
    for sale in sales_data:
        sale_date = datetime.strptime(sale['tanggal_penjualan'], '%d-%m-%Y')
        day_name = sale_date.strftime('%A')  # English day name
        indonesian_day_name = day_name_translation.get(day_name)  # Translate to Indonesian
        if indonesian_day_name:  # Ensure the day name is valid
            total_amount = sum(item['total_harga'] for item in sale['items'])
            daily_sales[indonesian_day_name] += total_amount

    # Get the total amount for the week
    weekly_total = sum(daily_sales.values())

    # Get the total amount for the last day
    last_day_total = daily_sales[day_name_translation[end_date.strftime('%A')]]

    # Prepare data for the chart
    sales_chart_data = []
    labels = []
    for i in range(7):
        day = (start_date + timedelta(days=i)).strftime('%A')
        indonesian_day_name = day_name_translation.get(day)
        labels.append(indonesian_day_name)
        sales_chart_data.append(daily_sales[indonesian_day_name])

    suppliers = db.suppliers.count_documents({})
    products = db.products.count_documents({})
    users = db.users.count_documents({"role": "user"})

    return render_template(
        'admin/dashboard.html',
        current_route=request.path,
        suppliers=suppliers,
        products=products,
        users=users,
        weekly_total=weekly_total,
        last_day_total=last_day_total,
        sales_chart_data=sales_chart_data,
        labels=labels
    )
