# SP Backend Project Structure

```
sp-backend/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── models.py                   # Database models (SQLAlchemy)
├── routes.py                   # API endpoints/blueprints
├── utils.py                    # Utility functions (Excel parsing)
├── admin.html                  # Admin dashboard UI
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
├── start_server.bat           # Windows startup script
├── start_server.sh            # Linux/Mac startup script
├── create_sample_excel.py     # Generate sample Excel file
├── README.md                  # Basic API documentation
├── SETUP.md                   # Quick setup guide
├── INTEGRATION_GUIDE.md       # Flutter integration guide
├── uploads/                   # Uploaded Excel files (auto-created)
├── sp_products.db            # SQLite database (auto-created)
└── venv/                      # Virtual environment (auto-created)
```

## 📄 File Descriptions

### Core Application Files

**app.py**
- Main Flask application entry point
- Initializes database, CORS, and blueprints
- Serves admin dashboard on `/`
- Run with: `python app.py`

**config.py**
- Development and Production configurations
- Database URI settings
- Upload folder configuration
- Max file size limits

**models.py**
- SQLAlchemy database models
- `Product` model with all fields
- JSON serialization support (`to_dict()`)
- Database relationships and constraints

**routes.py**
- RESTful API endpoints
- Product CRUD operations
- Excel file upload handling
- Search and filter functionality
- Statistics endpoints

**utils.py**
- Excel file parsing logic
- Product data validation
- Database save operations
- Error handling for data import

### User Interface

**admin.html**
- Beautiful web-based admin dashboard
- File upload with drag-and-drop
- Real-time statistics display
- Responsive design (mobile-friendly)
- Access at: http://localhost:5000

### Configuration Files

**requirements.txt**
- Python package dependencies
- Flask 2.3.0
- Flask-SQLAlchemy 3.0.0
- openpyxl for Excel handling
- python-dotenv for environment variables

**.env.example**
- Template for environment variables
- Copy to `.env` for local development
- Stores sensitive configuration

**.gitignore**
- Prevents committing unnecessary files
- Ignores `__pycache__`, `venv`, `.db` files
- Ignores uploaded files and logs

### Setup & Documentation

**setup_server.bat** (Windows)
- One-click startup script
- Automatically creates virtual environment
- Installs dependencies
- Starts the server

**start_server.sh** (Mac/Linux)
- Bash startup script
- Same functionality as batch file
- Make executable: `chmod +x start_server.sh`

**create_sample_excel.py**
- Generates sample product Excel file
- Formatted with headers and sample data
- Useful for testing upload functionality
- Creates: `sample_products.xlsx`

## 📚 Documentation Files

**README.md**
- API endpoint documentation
- Excel file format specification
- Usage examples from Flutter
- Database information
- Basic troubleshooting

**SETUP.md**
- Quick start guide
- Backend startup instructions
- Excel file format
- Flask Flask app integration
- Troubleshooting tips

**INTEGRATION_GUIDE.md**
- Complete integration guide
- Flutter app setup
- API provider examples
- Deployment options
- Production security notes
- Advanced troubleshooting

## 🗂️ Auto-Generated Directories

**uploads/**
- Stores uploaded Excel files temporarily
- Auto-created on first upload
- Files auto-deleted after processing

**venv/**
- Python virtual environment
- Created by startup scripts
- Contains all dependencies
- Should be in `.gitignore`

**sp_products.db**
- SQLite database file
- Stores all product data
- Auto-created on first run
- Can be deleted to reset database

## 🔄 Data Flow

```
User (Admin)
    ↓
Open http://localhost:5000 (admin.html)
    ↓
Select & Upload Excel file (.xlsx)
    ↓
app.py → routes.py (POST /products/upload)
    ↓
utils.py (parse_excel_products)
    ↓
Validate data → models.py (Product)
    ↓
Save to sp_products.db
    ↓
Return success message
    ↓
Flutter App
    ↓
GET /api/products
    ↓
Receive ProductModel list
    ↓
Display in UI
```

## 🚀 Quick Start Commands

```bash
# Window: Double-click
start_server.bat

# Mac/Linux: Run script
./start_server.sh

# Or manually:
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## 📡 API Base URL

- **Local (Emulator):** `http://localhost:5000/api`
- **Local (Device):** `http://192.168.x.x:5000/api`
- **Cloud:** `https://yourdomain.com/api`

## 📝 Key Features

✅ Excel file upload
✅ Product CRUD operations
✅ Search and filtering
✅ Category management
✅ Inventory statistics
✅ Admin dashboard
✅ CORS enabled
✅ Error handling
✅ Duplicate detection
✅ RESTful API design

## 🔐 Security Considerations

- CORS enabled for development
- No authentication (development mode)
- HTTP only (development)
- Add JWT tokens for production
- Enable HTTPS for production
- Validate file uploads
- Rate limit endpoints
- Use environment variables for secrets

## 💾 Database Schema

```
Product Table:
- id (UUID, Primary Key)
- code (String, Unique)
- name (String)
- description (Text)
- category (String)
- costPrice (Float)
- sellingPrice (Float)
- stockLevel (Integer)
- reorderLevel (Integer)
- createdAt (DateTime)
- updatedAt (DateTime)
```

## 🎯 Next Steps

1. ✅ Start backend: `python app.py`
2. ✅ Open admin: `http://localhost:5000`
3. ✅ Create/upload Excel file
4. ✅ Update Flutter app API URL
5. ✅ Run Flutter app
6. ✅ Test product loading

**Ready to scale your POS system! 🎉**
