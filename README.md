# Project Script &mdash; Render Ready Web Application

A lightweight, production-ready Python web application that runs a script generating and printing numbers from **1 to 1000**. Designed for instant, free deployment on [Render.com](https://render.com).

---

## 📁 Project Structure

```text
project-script/
├── script.py          # Core Python script (prints numbers 1 to 1000)
├── app.py             # Flask Web Application & Interactive UI Dashboard
├── requirements.txt   # Dependencies (Flask, Gunicorn)
├── Procfile           # Process declaration for Render
├── render.yaml        # Render Blueprint (Infrastructure as Code)
└── README.md          # Deployment & usage instructions
```

---

## 🚀 How to Deploy on Render (Step-by-Step)

### Option A: Manual Setup (Recommended & Easiest)

1. **Push to GitHub**:
   * Create a new repository on GitHub named `project-script`.
   * Push all files from this `project-script` folder to your GitHub repository:
     ```bash
     cd c:/Users/manvi/OneDrive/Desktop/newp/project-script
     git init
     git add .
     git commit -m "Initial commit for Render deployment"
     git branch -M main
     git remote add origin https://github.com/<YOUR_USERNAME>/project-script.git
     git push -u origin main
     ```

2. **Log into Render**:
   * Go to [https://dashboard.render.com](https://dashboard.render.com).
   * Sign up or log in (you can log in directly with GitHub).

3. **Create Web Service**:
   * Click the **"New +"** button in the top navigation and select **"Web Service"**.
   * Select **"Build and deploy from a Git repository"** and click **Next**.
   * Connect your GitHub account and select the `project-script` repository.

4. **Configure the Service**:
   * **Name**: `project-script` (or any name you prefer)
   * **Region**: Oregon (US West) or Frankfurt (EU)
   * **Branch**: `main`
   * **Runtime**: `Python 3`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `gunicorn app:app`
   * **Instance Type**: Select **Free** ($0/month)

5. **Deploy**:
   * Click **"Deploy Web Service"** at the bottom of the page.
   * Render will automatically install dependencies and start the application.
   * In 1–2 minutes, Render will provide your public live URL (e.g., `https://project-script-xxxx.onrender.com`).

---

### Option B: 1-Click Blueprint Deployment

Because this repository contains `render.yaml`, you can also deploy using Render Blueprints:
1. In Render Dashboard, click **"New +" ➔ "Blueprint"**.
2. Select your `project-script` repository.
3. Render will read `render.yaml` and configure everything automatically!

---

## 💻 Running Locally on Your Machine

### 1. Run the Python Script directly in Terminal:
```powershell
cd c:\Users\manvi\OneDrive\Desktop\newp\project-script
python script.py
```

### 2. Run the Web App locally:
```powershell
cd c:\Users\manvi\OneDrive\Desktop\newp\project-script
pip install -r requirements.txt
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your browser. Click **"Run Script (1 to 1000)"** to view the live execution!
