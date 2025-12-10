# Krishna Medical Store Billing System - Version 3.0 Roadmap

Building on the solid foundation of v2.0, Version 3.0 aims to bring **Professional Store Management** and **Analytics** to the system.

## 🚀 Key Features for V03

### 1. 📊 Advanced Dashboard & Analytics
- **Sales Charts**: Visual graphs for Daily, Weekly, and Monthly sales trends.
- **Top Products**: Identify best-selling medicines and high-margin items.
- **Low Stock Alerts**: Dedicated dashboard widget for critical stock warnings.
- **Profit/Loss Report**: Automatic calculation based on Purchase Price vs. Selling Price.

### 2. 🔐 User Roles & Security
- **Multi-User Login**: Separate accounts for **Admin** (Owner) and **Staff**.
- **Permissions**: Restrict Staff from deleting products or viewing total profit.
- **Audit Logs**: Track who deleted an invoice or modified stock.

### 3. 💾 Database Upgrade (Critical)
- **Migrate to SQLite/SQL**: Move away from CSV files to a proper SQL database.
    - **Why?** Faster performance, prevents data corruption, allows complex queries, and supports concurrent users.

### 4. 📲 Digital Integration
- **WhatsApp Invoicing**: Send PDF bills directly to user's WhatsApp (via API or Web automation).
- **Barcode Scanning**: Native support for USB Barcode Scanners for ultra-fast billing.
- **Email Reports**: Auto-email daily sales summaries to the owner.

### 5. 🚚 Supplier & Purchase Management
- **Purchase Entry**: Record stock arrival from distributors (not just manual stock adjustment).
- **Supplier Ledger**: Track how much you owe to each distributor.
- **Expiry Management**: First-In-First-Out (FIFO) tracking for medicine batches.

### 6. 🧾 GST & Compliance
- **GSTR Reports**: One-click generation of Excel sheets for GST filing (GSTR-1).
- **HSN Code Summary**: Category-wise sales breakdown.

## 📅 Suggested Phasing

- **Phase 1 (Core Tech)**: Database Migration (CSV -> SQL).
- **Phase 2 (Management)**: Supplier Module & Role-based Login.
- **Phase 3 (Growth)**: WhatsApp/Email integrations and Analytics Dashboard.
