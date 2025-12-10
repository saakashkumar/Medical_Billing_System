# Krishna Medical Store Billing System v2.0

A modern, responsive web-based billing and inventory management application designed for pharmacies. Built with **Python (Flask)** and **Vanilla JavaScript/CSS**.

## 🚀 Key Features

### 🧾 Smart Billing
- **Real-time Search**: Instantly find medicines by name.
- **Auto-Fill**: Customer mobile and name lookup.
- **Flexible Units**: Sell by **Strip** or **Loose Tablet**.
- **Invoice Generation**: Auto-calculates totals, taxes, and saves invoices to PDF/Print.

### 📦 Inventory Management
- **Grid & List Views**: Toggle between premium product cards and compact rows.
- **Search & Filter**: Filter by Category or search by Name/Batch.
- **Stock Tracking**: Visual indicators for Low Stock and Expiry warnings.
- **Infinite Scroll**: Smoothly browse thousands of products.

### 📱 Modern UI
- **Responsive Design**: Works on Desktop, Tablet, and Mobile.
- **Premium Aesthetics**: Clean cards, sticky headers, and smooth animations.
- **Full Page Scroll**: Natural, app-like scrolling experience.

---

## 🛠️ Setup & Installation

1.  **Prerequisites**:
    - Python 3.x installed.
    - `pip` (Python package manager).

2.  **Install Dependencies**:
    ```bash
    pip install flask
    ```

3.  **Run the Application**:
    - Double-click `Launch_Billing.bat` 
    - OR run manually:
    ```bash
    python app.py
    ```

4.  **Access the App**:
    - Open your browser and go to: `http://127.0.0.1:5000`

---

## 📂 Project Structure

- **`app.py`**: Main Flask backend (Handling API & Routes).
- **`product/`**: CSV Database for Products and Backups.
- **`customers.csv`**: Database of customer details.
- **`invoices/`**: Generated PDF/HTML invoices.
- **`static/`**:
    - `css/style.css`: All styling (Responsive, Grid, Cards).
    - `js/script.js`: Frontend logic (Search, Cart, Infinite Scroll).
- **`templates/`**: HTML pages (`billing.html`, `inventory.html`).

---

## 📝 Usage Guide

### Billing Page
1.  **Search**: Start typing a medicine name (it auto-focuses).
2.  **Add**: Click "Add +" on a card.
3.  **Cart**:
    - Adjust **Qty** or **Price** directly.
    - Switch Unit (Strip/Loose) if applicable.
4.  **Checkout**: Enter Customer Name/Mobile -> Click **Generate Invoice**.

### Inventory Page
1.  **View**: Click "List/Grid" to choose your preferred layout.
2.  **Edit**: Click any product to update Price/Stock.
3.  **Add**: Use the "Add Product" button for new stock.
