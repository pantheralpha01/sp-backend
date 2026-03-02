# 🚀 Backend Setup - Quick Start (5 Minutes)

## Step 1: Start the Backend

### Windows Users:
- Open File Explorer
- Navigate to: `C:\Users\Acer\Desktop\sp-backend`
- **Double-click:** `start_server.bat`
- Wait for the terminal to show "Flask server on localhost:5000"

### Mac/Linux Users:
```bash
cd sp-backend
chmod +x start_server.sh
./start_server.sh
```

## Step 2: Open Admin Dashboard

While backend is running:
- Open browser
- Go to: **http://localhost:5000**
- You should see the admin dashboard

## Step 3: Create Sample Products

In the sp-backend folder, run:
```bash
python create_sample_excel.py
```

This creates `sample_products.xlsx` with sample data.

## Step 4: Upload Products

1. In admin dashboard, click upload area
2. Select `sample_products.xlsx` or your own Excel file
3. Click "Upload Products"
4. Wait for success message
5. Products now available on app!

## Step 5: Connect Flutter App

Edit this file: [lib/core/services/api_service.dart](../lib/core/services/api_service.dart)

Change:
```dart
const String API_BASE_URL = 'http://localhost:5000/api';
```

For **physical device** (on same WiFi):
```dart
const String API_BASE_URL = 'http://192.168.1.100:5000/api';
// Change 192.168.1.100 to your computer's IP
```

Get your IP: Type `ipconfig` in Command Prompt (Windows)

## Step 6: Run Flutter App

```bash
flutter pub get
flutter run
```

Products should now load from the backend! ✅

---

## 📋 Excel File Format

Your Excel file needs these columns:

| Column Name | Type | Required? | Example |
|-------------|------|-----------|---------|
| code | Text | YES | SKU001 |
| name | Text | YES | Laptop |
| sellingPrice | Number | YES | 75000 |
| category | Text | No | Electronics |
| costPrice | Number | No | 45000 |
| stockLevel | Number | No | 10 |
| reorderLevel | Number | No | 3 |
| description | Text | No | High performance |

**Minimum required:** code, name, sellingPrice

---

## 🎯 What You Now Have

✅ **Backend Server** - Handles product management
✅ **Admin Dashboard** - Upload products via Excel
✅ **SQLite Database** - Stores all products
✅ **REST API** - Flutter app calls endpoints
✅ **CORS Enabled** - Cross-origin requests work
✅ **Error Handling** - Invalid data handled gracefully

---

## 🔧 Troubleshooting

**Backend won't start?**
- Python 3.7+ installed?
- Run: `python --version`

**Can't access http://localhost:5000?**
- Is terminal still running?
- Is port 5000 blocked by firewall?

**Flutter app can't connect?**
- Check API URL is correct
- On device: use your computer IP, not localhost
- Check both on same WiFi

**Excel upload fails?**
- Check file is `.xlsx` (not `.csv` or `.xls`)
- Ensure headers are in first row
- Check required columns: code, name, sellingPrice

**Products not showing in app?**
- Did upload complete successfully?
- Restart Flutter app after upload
- Check API health: http://localhost:5000/api/health

---

## 📚 More Documentation

- **README.md** - Full API reference
- **SETUP.md** - Detailed setup guide
- **INTEGRATION_GUIDE.md** - Complete Flutter integration
- **PROJECT_STRUCTURE.md** - File descriptions
- **admin.html** - Admin dashboard source

---

## 🎓 Next: Connect Your App

Once backend is working:

1. Update Flutter app API URL
2. Import `api_service.dart` in your providers
3. Use `productsFromApiProvider` to fetch products
4. Deploy to production when ready

**That's it! You're ready to scale! 🎉**
