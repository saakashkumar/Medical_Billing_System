from flask import Flask, render_template, jsonify, request
import csv
import os
from datetime import datetime

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCT_FILE = os.path.join(BASE_DIR, 'product', 'product.csv')
INVOICE_DIR = os.path.join(BASE_DIR, 'invoices')

# Ensure invoice directory exists
os.makedirs(INVOICE_DIR, exist_ok=True)

@app.route('/')
def index():
    """Serve the main billing page."""
    return render_template('billing.html')

@app.route('/api/products')
def get_products():
    """Read products from CSV and return as JSON."""
    products = []
    if os.path.exists(PRODUCT_FILE):
        try:
            with open(PRODUCT_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Clean and parse data
                    try:
                        products.append({
                            'id': row.get('id', ''),
                            'name': row.get('name', 'Unknown'),
                            'price': float(row.get('price', 0)),
                            'stock': float(row.get('stock', 0)),
                            'unit': row.get('unit', 'Strip'),
                            'type': row.get('type', 'Tablet'),
                            'category': row.get('category', 'General'),
                            'batch': row.get('batch', ''),
                            'expiry': row.get('expiry', ''),
                            'gst_rate': row.get('gst_rate', '0'),
                            'per_strip': row.get('per_strip', '')
                        })
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify(products)

@app.route('/api/invoice', methods=['POST'])
def create_invoice():
    """Generate invoice, update stock, and log sale."""
    data = request.json
    customer_name = data.get('customer_name', 'Walk-in')
    customer_mobile = data.get('customer_mobile', '')
    items = data.get('items', [])
    
    if not items:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400

    # 1. Load current stock to check availability and prepare update
    product_map = {} # id -> row dict
    all_products = []
    
    try:
        if os.path.exists(PRODUCT_FILE):
            with open(PRODUCT_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    product_map[row['id']] = row
                    all_products.append(row)
        else:
            return jsonify({'success': False, 'message': 'Product file not found'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error reading products: {e}"}), 500

    # 2. Validation & Calculation
    total_amount = 0.0
    invoice_items = []

    for item in items:
        pid = str(item.get('id'))
        req_qty = float(item.get('qty', 0))
        
        if pid not in product_map:
            continue # Skip invalid items
            
        prod = product_map[pid]
        current_stock = float(prod['stock'])
        
        if current_stock < req_qty:
            return jsonify({'success': False, 'message': f"Insufficent stock for {prod['name']}"}), 400
            
        # Update stock in memory object
        prod['stock'] = str(current_stock - req_qty)
        
        # Calculate
        # Use price from request if available (Override), else DB price
        # Calculate
        mrp = float(prod.get('price', 0)) # Original DB Price is MRP
        price = float(item.get('price', mrp)) # Use override price if present (Selling Price)
        qty = req_qty
        
        # GST Calc (Back-calculate from Total assuming Inclusive, or Add on top?)
        # Let's assume the Price entered is the Final Price (Inclusive)
        # Base = Price / (1 + Rate/100)
        gst_rate = float(prod.get('gst_rate', 0))
        net_amount = price * qty
        
        # If price is inclusive:
        base_amount = net_amount / (1 + (gst_rate/100))
        tax_amount = net_amount - base_amount
        
        total_amount += net_amount
        
        invoice_items.append({
            'name': prod['name'],
            'qty': qty,
            'mrp': mrp,
            'price': price,
            'total': net_amount,
            'batch': prod.get('batch', ''),
            'expiry': prod.get('expiry', ''),
            'gst_rate': gst_rate,
            'tax_amt': tax_amount,
            'base_amt': base_amount
        })

    # 3. Save Invoice File
    lines = []
    lines.append("================================================")
    lines.append("             KRISHNA MEDICAL STORE")
    lines.append("================================================")
    now = datetime.now()
    lines.append(f"Date: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Customer: {customer_name}")
    if customer_mobile:
        lines.append(f"Mobile:   {customer_mobile}")
    lines.append("------------------------------------------------")

    # --- SAVE CUSTOMER LOGIC ---
    try:
        customers = []
        if os.path.exists(CUSTOMER_FILE):
            with open(CUSTOMER_FILE, 'r', encoding='utf-8') as f:
                customers = list(csv.DictReader(f))
        
        # Check if exists (match by Mobile if present, else Name)
        existing_cust = None
        if customer_mobile:
             existing_cust = next((c for c in customers if c.get('mobile') == customer_mobile), None)
        
        if not existing_cust:
             existing_cust = next((c for c in customers if c['name'].lower() == customer_name.lower()), None)

        if existing_cust:
            # Update existing
            existing_cust['visits'] = str(int(existing_cust.get('visits', 0)) + 1)
            existing_cust['total_spent'] = str(float(existing_cust.get('total_spent', 0)) + total_amount)
            if customer_mobile and not existing_cust.get('mobile'):
                existing_cust['mobile'] = customer_mobile # Update mobile if missing
        else:
            # Create new
            new_id = str(len(customers) + 1)
            customers.append({
                'id': new_id,
                'name': customer_name,
                'mobile': customer_mobile,
                'address': '',
                'visits': '1',
                'total_spent': str(total_amount)
            })

        # Write back
        cust_fieldnames = ['id', 'name', 'mobile', 'address', 'visits', 'total_spent']
        with open(CUSTOMER_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=cust_fieldnames)
            writer.writeheader()
            writer.writerows(customers)

    except Exception as e:
        print(f"Error saving customer: {e}")
        # Don't fail the invoice for this, just log it
    # ---------------------------
    lines.append(f"{'Item':<15} {'Qty':<4} {'MRP':<7} {'Rate':<7} {'Total':<8}")
    lines.append("------------------------------------------------")
    
    total_tax = 0.0
    
    for item in invoice_items:
        lines.append(f"{item['name'][:15]:<15} {item['qty']:<4} {item['mrp']:<7} {item['price']:<7} {item['total']:<8}")
        # if item['gst_rate'] > 0:
        #     lines.append(f"   Batch:{item['batch']} Exp:{item['expiry']} GST:{int(item['gst_rate'])}%")
        # else:
        lines.append(f"   Batch:{item['batch']} Exp:{item['expiry']}")
        total_tax += item['tax_amt']

    lines.append("------------------------------------------")
    # lines.append(f"Sub Total (Taxable):  {total_amount - total_tax:.2f}")
    # lines.append(f"Total GST:            {total_tax:.2f}")
    lines.append(f"GRAND TOTAL:          {total_amount:.2f}")
    lines.append("==========================================")
    lines.append("   Thank you for your business!")
    
    safe_name = "".join([c for c in customer_name if c.isalpha() or c.isdigit() or c==' ']).strip()
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    filename = f"{safe_name}_{timestamp}.txt"
    filepath = os.path.join(INVOICE_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
            
        # 4. Commit Stock Update to CSV
        with open(PRODUCT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_products)
            
        # 5. Log Sale
        sales_file = os.path.join(BASE_DIR, 'sales.csv')
        file_exists = os.path.exists(sales_file)
        with open(sales_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['date', 'time', 'customer', 'amount', 'invoice'])
            writer.writerow([
                now.strftime('%Y-%m-%d'), 
                now.strftime('%H:%M:%S'), 
                customer_name, 
                total_amount, 
                filename
            ])
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'File Error: {e}'}), 500

    return jsonify({'success': True, 'invoice_file': filename, 'total': total_amount})

@app.route('/api/dashboard')
def dashboard_stats():
    """Return sales stats and low stock items."""
    # 1. Calc Sales for Today
    today = datetime.now().strftime('%Y-%m-%d')
    total_sales = 0.0
    today_count = 0
    recent_txns = []
    
    sales_file = os.path.join(BASE_DIR, 'sales.csv')
    if os.path.exists(sales_file):
        try:
            with open(sales_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                for row in reversed(rows): # most recent first
                    if row['date'] == today:
                        total_sales += float(row['amount'])
                        today_count += 1
                    
                    if len(recent_txns) < 5:
                        recent_txns.append(row)
        except Exception:
            pass

    # 2. Get Low Stock
    low_stock = []
    if os.path.exists(PRODUCT_FILE):
        try:
            with open(PRODUCT_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        if int(row['stock']) < 10:
                            low_stock.append(row)
                    except ValueError:
                        pass
        except Exception:
            pass
            
    return jsonify({
        'sales_today': total_sales,
        'orders_today': today_count,
        'low_stock': low_stock,
        'recent': recent_txns
    })

@app.route('/api/product', methods=['POST', 'PUT', 'DELETE'])
def manage_product():
    """CRUD operations for products."""
    try:
        data = request.get_json(silent=True) or {}
        method = request.method
        
        # Load all products
        products = []
        if os.path.exists(PRODUCT_FILE):
            with open(PRODUCT_FILE, 'r', encoding='utf-8') as f:
                products = list(csv.DictReader(f))
                
        fieldnames = ['id', 'name', 'price', 'stock', 'unit', 'type', 'category', 'batch', 'expiry', 'gst_rate', 'per_strip']
        
        if method == 'DELETE':
            pid = request.args.get('id')
            if not pid and request.json:
                pid = request.json.get('id')
            
            pid = str(pid).strip() if pid else None
            
            print(f"DEBUG: DELETE ID: {pid}")
            products = [p for p in products if p['id'] != pid]
            
        elif method == 'POST':
            new_id = str(len(products) + 1)
            # Handle manual ID if provided and unique? No, auto-increment simple
            if any(p['id'] == new_id for p in products):
                new_id = str(int(new_id) + 1000) # Simple collision avoidance

            products.append({
                'id': new_id,
                'name': data.get('name'),
                'price': data.get('price'),
                'stock': data.get('stock'),
                'unit': data.get('unit', '-'),
                'type': data.get('type', '-'),
                'category': data.get('category', '-'),
                'batch': data.get('batch', ''),
                'expiry': data.get('expiry', ''),
                'gst_rate': data.get('gst_rate', '0'),
                'per_strip': data.get('per_strip', '')
            })
            
        elif method == 'PUT':
            pid = str(data.get('id'))
            for p in products:
                if p['id'] == pid:
                    p['name'] = data.get('name', p['name'])
                    p['price'] = data.get('price', p['price'])
                    p['stock'] = data.get('stock', p['stock'])
                    p['unit'] = data.get('unit', p.get('unit','-'))
                    p['type'] = data.get('type', p.get('type','-'))
                    p['category'] = data.get('category', p.get('category','-'))
                    p['batch'] = data.get('batch', p.get('batch', ''))
                    p['expiry'] = data.get('expiry', p.get('expiry', ''))
                    p['gst_rate'] = data.get('gst_rate', p.get('gst_rate', '0'))
                    p['per_strip'] = data.get('per_strip', p.get('per_strip', ''))
                    break
                    
        # Save
        with open(PRODUCT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(products)
            
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/print_invoice/<filename>')
def print_invoice(filename):
    """Serve printer friendly invoice."""
    path = os.path.join(INVOICE_DIR, filename)
    if not os.path.exists(path):
        return "Invoice not found", 404
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    return render_template('print_invoice.html', content=content)

@app.route('/inventory')
def inventory_page():
    return render_template('inventory.html')

@app.route('/customers')
def customers_page():
    return render_template('customers.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

CUSTOMER_FILE = os.path.join(BASE_DIR, 'customers.csv')

@app.route('/api/customers')
def get_customers():
    """Aggregate customers from sales.csv and merge with profile data."""
    customers = {} # name -> {name, total_spent, visits, last_visit, mobile, address, id}
    
    # 1. Load Sales History
    sales_file = os.path.join(BASE_DIR, 'sales.csv')
    if os.path.exists(sales_file):
        try:
            with open(sales_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row['customer']
                    try:
                        amt = float(row['amount'])
                    except ValueError:
                        amt = 0.0
                        
                    if name not in customers:
                        customers[name] = {
                            'name': name, 
                            'total_spent': 0.0, 
                            'visits': 0, 
                            'last_visit': '',
                            'mobile': '', 
                            'address': '',
                            'id': ''
                        }
                    
                    customers[name]['total_spent'] += amt
                    customers[name]['visits'] += 1
                    customers[name]['last_visit'] = row['date']
        except Exception:
            pass
            
    # 2. Load Profiles and Merge
    if os.path.exists(CUSTOMER_FILE):
        try:
            with open(CUSTOMER_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Construct full name to match
                    full_name = f"{row['first_name']} {row['last_name']}".strip()
                    if full_name in customers:
                        customers[full_name]['mobile'] = row.get('mobile', '')
                        customers[full_name]['address'] = row.get('address', '')
                        customers[full_name]['id'] = row.get('id', '')
                    else:
                        # Add profile even if no sales yet
                        customers[full_name] = {
                            'name': full_name,
                            'total_spent': 0.0,
                            'visits': 0,
                            'last_visit': 'Never',
                            'mobile': row.get('mobile', ''),
                            'address': row.get('address', ''),
                            'id': row.get('id', '')
                        }
        except Exception:
            pass

    return jsonify(list(customers.values()))

@app.route('/api/customer_profile', methods=['POST'])
def save_profile():
    try:
        data = request.json
        pid = str(data.get('id', '')).strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        mobile = data.get('mobile', '').strip()
        address = data.get('address', '').strip()
        
        if not first_name:
             return jsonify({'success': False, 'message': 'First Name is required'}), 400

        profiles = []
        if os.path.exists(CUSTOMER_FILE):
            with open(CUSTOMER_FILE, 'r', encoding='utf-8') as f:
                 profiles = list(csv.DictReader(f))
        
        updated = False
        
        # 1. Try to find by ID
        if pid:
            for p in profiles:
                if p['id'] == pid:
                    p['first_name'] = first_name
                    p['last_name'] = last_name
                    p['mobile'] = mobile
                    p['address'] = address
                    updated = True
                    break
        
        # 2. If no ID or ID not found (fallback to Name match to prevent duplicates if user didn't have ID yet)
        if not updated:
            for p in profiles:
                if p['first_name'].lower() == first_name.lower() and p['last_name'].lower() == last_name.lower():
                    p['mobile'] = mobile
                    p['address'] = address
                    updated = True
                    break
        
        if not updated:
            new_id = str(len(profiles) + 1)
            profiles.append({
                'id': new_id,
                'first_name': first_name,
                'last_name': last_name,
                'mobile': mobile,
                'address': address
            })
            
        with open(CUSTOMER_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id','first_name','last_name','mobile','address'])
            writer.writeheader()
            writer.writerows(profiles)
            
        # 3. Handle Historical Name Change (Refactor in sales.csv)
        old_name = data.get('old_name', '').strip()
        new_full_name = f"{first_name} {last_name}".strip()
        
        if old_name and old_name != new_full_name:
            sales_file = os.path.join(BASE_DIR, 'sales.csv')
            if os.path.exists(sales_file):
                sales_rows = []
                sales_updated = False
                try:
                    with open(sales_file, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        sales_rows = list(reader)
                        
                    # Skip header row 0
                    for i in range(1, len(sales_rows)):
                        if len(sales_rows[i]) >= 3 and sales_rows[i][2] == old_name:
                             sales_rows[i][2] = new_full_name # Update customer column
                             sales_updated = True
                             
                    if sales_updated:
                        with open(sales_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerows(sales_rows)
                except Exception as e:
                    print(f"Error updating sales log: {e}")

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customer_history')
def get_customer_history():
    name = request.args.get('name')
    history = []
    sales_file = os.path.join(BASE_DIR, 'sales.csv')
    
    if os.path.exists(sales_file):
        try:
            with open(sales_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['customer'] == name:
                        history.append(row)
        except Exception:
            pass
    return jsonify(history)


@app.route('/reports')
def reports_page():
    return render_template('reports.html')

@app.route('/api/reports')
def get_reports():
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    if not start_str or not end_str:
        return jsonify([])
        
    start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    
    results = []
    
    sales_file = os.path.join(BASE_DIR, 'sales.csv')
    if os.path.exists(sales_file):
        try:
             with open(sales_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Row date format is YYYY-MM-DD
                    row_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                    if start_date <= row_date <= end_date:
                        results.append({
                            'date': row['date'],
                            'time': row['time'],
                            'customer': row['customer'],
                            'invoice': row['invoice'],
                            'amount': float(row['amount'])
                        })
        except Exception:
            pass
            
    return jsonify(results)

@app.route('/print_report')
def print_report_view():
    # Reuse filtering logic or just render template that calls API?
    # Better to serve static printable HTML for simplicity
    start = request.args.get('start')
    end = request.args.get('end')
    return f"""
    <html>
    <body onload="window.print()">
        <h2>Sales Report: {start} to {end}</h2>
        <div id="content">Loading data...</div>
        <script>
            fetch('/api/reports?start={start}&end={end}')
            .then(r=>r.json())
            .then(data => {{
                let total = 0;
                let html = '<table border="1" style="width:100%;border-collapse:collapse;text-align:left;"><thead><tr><th>Date</th><th>Customer</th><th>Invoice</th><th>Amount</th></tr></thead><tbody>';
                data.forEach(row => {{
                    total += row.amount;
                    html += `<tr><td>${{row.date}}</td><td>${{row.customer}}</td><td>${{row.invoice}}</td><td>${{row.amount}}</td></tr>`;
                }});
                html += `</tbody></table><h3>Total Revenue: ${{total}}</h3>`;
                document.getElementById('content').innerHTML = html;
            }});
        </script>
    </body>
    </html>
    """
    
@app.route('/api/reorder_list')
def get_reorder_list():
    """Generates printable HTML for items with stock <= 10"""
    low_stock_items = []
    if os.path.exists(PRODUCT_FILE):
        with open(PRODUCT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row['stock']) <= 10:
                    low_stock_items.append(row)
    
    html = """
    <html>
    <head>
        <title>Low Stock Re-Order List</title>
        <style>
            body { font-family: sans-serif; padding: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #333; padding: 8px; text-align: left; }
            th { background: #eee; }
        </style>
    </head>
    <body onload="window.print()">
        <h2>⚠️ Low Stock Re-Order List</h2>
        <p>Generated on: """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """</p>
        <table>
            <thead>
                <tr>
                    <th>Item Name</th>
                    <th>Current Stock</th>
                    <th>Supplier / Batch</th>
                </tr>
            </thead>
            <tbody>
    """
    for item in low_stock_items:
        html += f"<tr><td>{item['name']}</td><td>{item['stock']} {item['unit']}</td><td>{item.get('batch','')}</td></tr>"
        
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    # Auto-open browser could be done here, but standard practice is separate script
    app.run(port=5000, debug=True)
