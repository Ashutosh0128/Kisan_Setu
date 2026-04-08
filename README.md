# Kisan Setu - Premium Farming Equipment Rental

A modern, "Agri-Premium" web application for renting agricultural machinery, now powered by a **Django Backend**.

## 🚀 How to Run Locally

### Option 1: Using the Startup Script (Easiest for Windows)
If you are on Windows, simply **double-click** the `run_server.bat` file in the project root. This will automatically:
1. Activate the correct virtual environment.
2. Start the Django development server at `http://127.0.0.1:8000/`.

### Option 2: Running from Terminal (Project Root)
Open your terminal in the project root and run:
```powershell
.\backend\venv\Scripts\python.exe backend\manage.py runserver 8000
```
Then open your browser and go to: `http://127.0.0.1:8000/`

### Option 3: Manual Startup (Inside Backend Folder)
1. Open terminal and `cd backend`.
2. Activate the virtual environment: `.\venv\Scripts\activate`.
3. Run the server: `python manage.py runserver 8000`.


## ✨ Key Features
- **Modern UI/UX**: Emerald and gold color palette for a premium agricultural feel.
- **Dark/Light Mode**: Toggle between "Day" and "Midnight Forest" themes.
- **INR Pricing**: Prices formatted in Indian Rupees (₹).
- **Responsive**: Optimized for mobile, tablet, and desktop.
