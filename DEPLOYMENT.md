# Deploying Krishna Medical Billing to Render

This guide explains how to deploy your application to Render using the configuration files we just created.

> [!WARNING]
> **Data Persistence**: Render's filesystem is **ephemeral**.
> Any files created or modified while the app is running (like `sales.csv`, `customers.csv`, `invoices/*.txt`) will be **DELETED** every time the app restarts or redeploys.
> For production use, you must switch to a database (like PostgreSQL) or use Render's Persistent Disk.

## Prerequisites

1.  **GitHub Account**: You need a GitHub account.
2.  **Render Account**: You need a Render account (which you have).

## Step 1: Push Code to GitHub

First, you need to push your local code to a new GitHub repository.

1.  Create a new repository on GitHub (e.g., `krishna-medical-billing`).
2.  Run the following commands in your terminal to push your code:

```bash
git init
git add .
git commit -m "Initial commit for Render deployment"
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/krishna-medical-billing.git
git push -u origin main
```

## Step 2: Deploy on Render

1.  Go to the [Render Dashboard](https://dashboard.render.com/).
2.  Click **New +** and select **Web Service**.
3.  Connect your GitHub account if you haven't already.
4.  Find your `krishna-medical-billing` repository and click **Connect**.
5.  Render will detect the `render.yaml` file (if you choose "Blueprint") or you can manually configure it:
    *   **Name**: `krishna-medical-billing`
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn app:app`
6.  Click **Create Web Service**.

## Step 3: Verify

Once the deployment finishes (it might take a few minutes), Render will give you a URL (e.g., `https://krishna-medical-billing.onrender.com`).
Click it to see your live application.
