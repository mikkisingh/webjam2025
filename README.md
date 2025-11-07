# Flask + React + Tailwind + SQLite Template

A minimal full-stack template with:
- **Backend**: Flask + SQLite + SQLAlchemy
- **Frontend**: React (Vite) + Tailwind CSS

---

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Backend runs on: `http://127.0.0.1:5000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: `http://127.0.0.1:5173`

---

## 📁 Project Structure

```
flask-react-template/
├── backend/
│   ├── run.py              # Entry point
│   ├── app.py              # Flask app & routes
│   ├── database.py         # SQLAlchemy setup
│   ├── models.py           # Database models
│   └── requirements.txt    # Python dependencies
│
└── frontend/
    ├── src/
    │   ├── App.jsx         # Main React component
    │   ├── main.jsx        # React entry point
    │   └── components/     # Reusable components
    ├── index.html
    ├── vite.config.js
    └── tailwind.config.js
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/`      | Health check |
| GET    | `/items` | Get all items |
| POST   | `/items` | Create item |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | Flask, SQLAlchemy |
| Database | SQLite |

---

## 📝 Notes

- CORS is enabled for `http://127.0.0.1:5173`
- Database file (`app.db`) is auto-created in the backend folder
- Tailwind CSS errors in the editor are normal and will work when running

---


