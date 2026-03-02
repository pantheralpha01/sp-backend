# SP POS Backend - Complete Integration Guide

## 📦 Backend Setup (Flask)

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Quick Start

#### Windows:
```bash
cd sp-backend
start_server.bat
```

#### Mac/Linux:
```bash
cd sp-backend
chmod +x start_server.sh
./start_server.sh
```

#### Manual (All Platforms):
```bash
cd sp-backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
python app.py
```

### Generate Sample Excel File

```bash
python create_sample_excel.py
```

This creates `sample_products.xlsx` with sample product data that you can use for testing.

---

## 🌐 Accessing the Admin Dashboard

Once the server is running:

**URL:** http://localhost:5000

You'll see a beautiful admin dashboard where you can:
- ✅ Upload Excel files with products
- 📊 View inventory statistics
- 📈 Monitor product counts and stock levels

### Admin Dashboard Features

1. **Upload Products**
   - Drag & drop or click to select Excel file
   - Real-time upload progress
   - Success/error feedback

2. **Statistics**
   - Total products count
   - Total stock units
   - Total inventory value (KES)
   - Low stock items count

3. **Excel Format Guide**
   - Required columns: `code`, `name`, `sellingPrice`
   - Optional columns: `category`, `description`, `costPrice`, `stockLevel`, `reorderLevel`

---

## 📱 Connecting Flutter App to Backend

### Step 1: Update API Base URL

If the backend is on your local machine, the default `localhost:5000` should work for the emulator.

For **physical devices**, update [lib/core/services/api_service.dart](../lib/core/services/api_service.dart):

```dart
// For physical device on same network:
const String API_BASE_URL = 'http://192.168.1.100:5000/api';
// Replace 192.168.1.100 with your computer's local IP address
```

**Find your computer's IP address:**
- Windows: `ipconfig` in Command Prompt
- Mac/Linux: `ifconfig` in Terminal

### Step 2: Use the API Provider in Your Code

The API service provides several ready-to-use providers:

```dart
// In your widget:
final productsAsync = ref.watch(productsFromApiProvider);

productsAsync.when(
  data: (products) => ListView.builder(
    itemCount: products.length,
    itemBuilder: (context, index) => ProductTile(
      product: products[index],
    ),
  ),
  loading: () => const CircularProgressIndicator(),
  error: (error, _) => Text('Error: $error'),
);
```

### Available Providers

```dart
// Get all products
final products = ref.watch(productsFromApiProvider);

// Search products
final searchResults = ref.watch(searchProductsApiProvider('laptop'));

// Get product by code (barcode)
final product = ref.watch(productByCodeProvider('SKU001'));

// Get categories
final categories = ref.watch(categoriesFromApiProvider);

// Get stats
final stats = ref.watch(statsFromApiProvider);

// Check API health
final isHealthy = ref.watch(apiHealthProvider);
```

### Step 3: Update Your Providers

Example of updating `products_provider.dart` to use the backend:

```dart
import 'package:sp/core/services/api_service.dart';

// Replace sample data with API call:
@riverpod
Future<List<ProductModel>> products(Ref ref) async {
  return ref.watch(productsFromApiProvider);
}
```

---

## 🚀 Deployment Options

### Option 1: Local Network (Development)
- Backend runs on your PC
- Flutter app connects via local IP
- Best for testing

### Option 2: Cloud Server (Production)
- Host backend on Heroku, AWS, DigitalOcean, etc.
- Update `API_BASE_URL` to cloud URL
- Scale to multiple users

### Option 3: Docker Container
Create a `Dockerfile`:
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t sp-backend .
docker run -p 5000:5000 sp-backend
```

---

## 📊 API Endpoints

All endpoints return JSON responses:

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products` | Get all products |
| GET | `/products?search=name` | Search by name/code |
| GET | `/products?category=Electronics` | Filter by category |
| GET | `/products/<id>` | Get specific product |
| GET | `/products/code/<code>` | Get by barcode code |
| POST | `/products/upload` | Upload Excel file |
| PUT | `/products/<id>` | Update product |
| DELETE | `/products/<id>` | Delete product |

### Utilities
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/categories` | Get all categories |
| GET | `/stats` | Get inventory statistics |
| GET | `/health` | Health check |

**Example API Call:**
```dart
final dio = Dio();
final response = await dio.get('http://localhost:5000/api/products');
final products = response.data['data'];
```

---

## 🔒 Security Notes

**For Production:**

1. **Enable HTTPS:**
   - Get SSL certificate
   - Update URLs to `https://`

2. **Add Authentication:**
   - Implement login API
   - Use JWT tokens
   - Protect upload endpoint

3. **Set CORS Properly:**
   - In `app.py`, restrict origins:
   ```python
   CORS(app, origins=['https://yourdomain.com'])
   ```

4. **Rate Limiting:**
   - Add Flask-Limiter
   - Prevent abuse

5. **Environment Variables:**
   - Keep secret keys secure
   - Use `.env` file (not in git)

---

## 🛠️ Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -i :5000
kill -9 <PID>
```

**Dependencies not installing:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**Database issues:**
```bash
# Reset database
rm sp_products.db
python app.py
```

### Flutter Connection Issues

**Can't connect to localhost:**
- Use Android emulator: `10.0.2.2` instead of `localhost`
- Python backend URL: `http://10.0.2.2:5000/api`

**SSL certificate errors:**
- For development: Disable SSL verification (careful!)
  ```dart
  Dio()..httpClientAdapter = HttpClientAdapter()
    ..onHttpClientCreate = (client) {
      client.badCertificateCallback = (_, __, ___) => true;
      return client;
    };
  ```

**CORS errors:**
- Check backend has CORS enabled
- Verify API URL is correct
- Check firewall allows port 5000

### Excel Upload Issues

**File not uploading:**
- Check file format: `.xlsx` or `.xls` (not `.csv`)
- Ensure headers row exists
- File size < 16MB

**Products not saving:**
- Check required columns: `code`, `name`, `sellingPrice`
- Verify no duplicate codes (or they'll update)
- Check database write permissions

---

## 📝 Example Excel Data

| code | name | category | costPrice | sellingPrice | stockLevel | reorderLevel |
|------|------|----------|-----------|--------------|------------|--------------|
| LAP001 | Dell Laptop | Electronics | 45000 | 75000 | 10 | 3 |
| MOU001 | Wireless Mouse | Accessories | 800 | 1500 | 50 | 10 |
| KEY001 | Mechanical Keyboard | Accessories | 2000 | 3500 | 30 | 8 |
| MON001 | 24" Monitor | Electronics | 8000 | 14000 | 5 | 2 |

---

## 🎓 Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [REST API Best Practices](https://restfulapi.net/)
- [Flutter Networking](https://flutter.dev/docs/development/data-and-backend/state-mgmt/intro)

---

## 📞 Support

If you encounter issues:

1. Check the logs in console/terminal
2. Verify backend is running: `http://localhost:5000/api/health`
3. Check Flutter app has correct API URL
4. Ensure firewall allows port 5000
5. Try resetting database and uploading fresh data

**Happy coding! 🚀**
