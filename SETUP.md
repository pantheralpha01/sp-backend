# Quick Setup Guide

## 🚀 Starting the Backend

### Option 1: Windows Users
Double-click `start_server.bat` to start the backend automatically.

### Option 2: Manual Setup
```bash
# Navigate to backend directory
cd sp-backend

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

### Option 3: Using create_sample_excel.py
```bash
# Generate sample Excel file with products
python create_sample_excel.py

# This creates: sample_products.xlsx
# You can then upload this file through the admin dashboard
```

---

## 📊 Admin Dashboard

Once the server is running:

1. Open browser: **http://localhost:5000**
2. You'll see the admin dashboard
3. Click "Upload Products" and select your Excel file
4. The products will be saved and available in the app

---

## 📱 Connecting Flutter App to Backend

Update your Flutter app to use the backend API:

### 1. Update `products_provider.dart`

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

// Add this constant
const String API_BASE_URL = 'http://localhost:5000/api';  // or your IP/domain

// Replace sample data with API call
@riverpod
Future<List<ProductModel>> productsProvider(Ref ref) async {
  try {
    final response = await http.get(
      Uri.parse('$API_BASE_URL/products?page=1&per_page=100'),
    );
    
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body);
      final List<dynamic> data = json['data'];
      return data.map((p) => ProductModel.fromJson(p)).toList();
    }
    throw Exception('Failed to load products');
  } catch (e) {
    print('Error: $e');
    return [];
  }
}
```

### 2. Add http package to pubspec.yaml

```yaml
dependencies:
  http: ^1.1.0
```

### 3. Update backend URL for your network

If running on a different machine:
- Replace `localhost` with your computer's IP address
- Example: `http://192.168.1.100:5000/api`

---

## 📥 Excel File Format

Create your Excel file with these columns:

| Column | Type | Required | Example |
|--------|------|----------|---------|
| code | Text | ✓ | SKU001 |
| name | Text | ✓ | Laptop |
| category | Text | | Electronics |
| description | Text | | High performance |
| costPrice | Number | | 45000 |
| sellingPrice | Number | ✓ | 75000 |
| stockLevel | Number | | 10 |
| reorderLevel | Number | | 3 |

**Run this to create a sample Excel:**
```bash
python create_sample_excel.py
```

---

## 🔧 Troubleshooting

**Backend won't start?**
- Ensure Python 3.7+ is installed
- Try: `python --version`
- Run: `pip install -r requirements.txt`

**Can't find http://localhost:5000?**
- Check if port 5000 is already in use
- Change port in `app.py`: `app.run(port=5001)`

**Flutter can't connect to backend?**
- Use your computer IP instead: `http://192.168.x.x:5000`
- Check firewall allows port 5000
- Ensure both are on same network

**Excel upload fails?**
- Check column names are exact (case-insensitive)
- Ensure sellingPrice has values for all products
- Max file size: 16MB

**Database issues?**
- Delete `sp_products.db` to reset
- Run: `python app.py`

---

## 📝 API Endpoints

Once backend is running:

- **Get all products:** `GET /api/products`
- **Search products:** `GET /api/products?search=laptop`
- **Get product by code:** `GET /api/products/code/SKU001`
- **Upload Excel:** `POST /api/products/upload`
- **Get categories:** `GET /api/categories`
- **Get stats:** `GET /api/stats`

---

## 🎯 Next Steps

1. ✅ Start backend server
2. ✅ Open http://localhost:5000
3. ✅ Generate/prepare Excel file
4. ✅ Upload products through admin dashboard
5. ✅ Update Flutter app to use API
6. ✅ Build and run Flutter app
7. ✅ Products should now load from backend!

**Happy selling! 🎉**
