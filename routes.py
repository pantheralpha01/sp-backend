from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from models import Product, db
from utils import parse_excel_products, save_products_to_db
import os

api = Blueprint('api', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'API is running'}), 200

@api.route('/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering"""
    try:
        # Query parameters
        category = request.args.get('category')
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        query = Product.query
        
        # Filter by category
        if category and category.lower() != 'all':
            query = query.filter_by(category=category)
        
        # Search by name or code
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Product.name.ilike(search_term)) | 
                (Product.code.ilike(search_term))
            )
        
        # Pagination
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        products = [product.to_dict() for product in paginated.items]
        
        return jsonify({
            'success': True,
            'data': products,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/products/code/<code>', methods=['GET'])
def get_product_by_code(code):
    """Get a product by code (for barcode scanning)"""
    try:
        product = Product.query.filter_by(code=code).first()
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/products/upload', methods=['POST'])
def upload_products():
    """Upload and parse Excel file with products"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Only Excel files (.xlsx, .xls) are allowed'
            }), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        from flask import current_app
        upload_dir = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Parse Excel file
        products, parse_errors = parse_excel_products(file_path)
        
        if not products:
            return jsonify({
                'success': False,
                'message': 'No valid products found',
                'errors': parse_errors
            }), 400
        
        # Save to database
        success_count, duplicate_count, save_errors = save_products_to_db(products)
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except:
            pass
        
        all_errors = parse_errors + save_errors
        
        return jsonify({
            'success': True,
            'message': 'Upload successful',
            'summary': {
                'total_processed': len(products),
                'successful': success_count,
                'duplicates_updated': duplicate_count,
                'errors_count': len(all_errors)
            },
            'errors': all_errors
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500

@api.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'category' in data:
            product.category = data['category']
        if 'costPrice' in data:
            product.costPrice = float(data['costPrice'])
        if 'sellingPrice' in data:
            product.sellingPrice = float(data['sellingPrice'])
        if 'stockLevel' in data:
            product.stockLevel = int(data['stockLevel'])
        if 'reorderLevel' in data:
            product.reorderLevel = int(data['reorderLevel'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product updated',
            'data': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/categories', methods=['GET'])
def get_categories():
    """Get all unique product categories"""
    try:
        categories = db.session.query(Product.category).distinct().all()
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({
            'success': True,
            'data': sorted(category_list)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/stats', methods=['GET'])
def get_stats():
    """Get product statistics"""
    try:
        total_products = Product.query.count()
        total_stock = db.session.query(db.func.sum(Product.stockLevel)).scalar() or 0
        total_value = db.session.query(
            db.func.sum(Product.stockLevel * Product.sellingPrice)
        ).scalar() or 0
        low_stock = Product.query.filter(
            Product.stockLevel <= Product.reorderLevel
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_products': total_products,
                'total_stock_units': int(total_stock),
                'total_inventory_value': float(total_value),
                'low_stock_items': low_stock
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
