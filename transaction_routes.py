from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Transaction, TransactionItem, Payment, Product, db
from datetime import datetime

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')


def _build_transaction(data, identity):
    """Create Transaction + children from a dict. Deducts stock. No commit."""
    txn = Transaction(
        id=data['id'],
        receipt_number=data['receiptNumber'],
        shift_id=data.get('shiftId'),
        cashier_id=data.get('cashierId', identity['id']),
        cashier_name=data.get('cashierName', identity['name']),
        subtotal=float(data.get('subtotal', 0)),
        discount_total=float(data.get('discountTotal', 0)),
        tax_total=float(data.get('taxTotal', 0)),
        grand_total=float(data['grandTotal']),
        payment_method=data.get('paymentMethod', 'cash'),
        is_split_bill=bool(data.get('isSplitBill', False)),
        status='completed',
        created_at=(
            datetime.fromisoformat(data['createdAt'])
            if data.get('createdAt') else datetime.utcnow()
        ),
        synced_at=datetime.utcnow(),
    )
    db.session.add(txn)

    for item_data in data.get('items', []):
        item = TransactionItem(
            transaction_id=txn.id,
            product_id=item_data.get('productId'),
            product_code=item_data['productCode'],
            product_name=item_data['productName'],
            quantity=int(item_data['quantity']),
            unit_price=float(item_data['unitPrice']),
            discount=float(item_data.get('discount', 0)),
            line_total=float(item_data['lineTotal']),
        )
        db.session.add(item)

        # Deduct stock from product table
        if item_data.get('productId'):
            product = Product.query.get(item_data['productId'])
            if product:
                product.stockLevel = max(0, product.stockLevel - item.quantity)

    for pmt_data in data.get('payments', []):
        pmt = Payment(
            transaction_id=txn.id,
            method=pmt_data['method'],
            amount=float(pmt_data['amount']),
            reference=pmt_data.get('reference', ''),
            phone_number=pmt_data.get('phoneNumber', ''),
            card_last4=pmt_data.get('cardLast4', ''),
        )
        db.session.add(pmt)

    return txn


# ---------------------------------------------------------------------------
# Single transaction sync
# ---------------------------------------------------------------------------

@transactions_bp.route('', methods=['POST'])
@jwt_required()
def sync_transaction():
    """Receive one transaction from Flutter.  Idempotent on transaction id."""
    identity = get_jwt_identity()
    data = request.get_json() or {}

    if not data.get('id') or not data.get('receiptNumber') or 'grandTotal' not in data:
        return jsonify({'success': False, 'message': 'id, receiptNumber and grandTotal are required'}), 400

    # Idempotency: return existing record if already synced
    existing = Transaction.query.get(data['id'])
    if existing:
        return jsonify({'success': True, 'message': 'Already synced', 'data': existing.to_dict()}), 200

    try:
        txn = _build_transaction(data, identity)
        db.session.commit()
        return jsonify({'success': True, 'data': txn.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# Batch sync (for offline queues)
# ---------------------------------------------------------------------------

@transactions_bp.route('/batch', methods=['POST'])
@jwt_required()
def sync_batch():
    """Receive many transactions at once.  Each is idempotent individually."""
    identity = get_jwt_identity()
    data = request.get_json() or {}
    transactions_data = data.get('transactions', [])

    results = {'synced': 0, 'skipped': 0, 'failed': 0, 'errors': []}

    for txn_data in transactions_data:
        if Transaction.query.get(txn_data.get('id')):
            results['skipped'] += 1
            continue
        try:
            _build_transaction(txn_data, identity)
            db.session.commit()
            results['synced'] += 1
        except Exception as e:
            db.session.rollback()
            results['failed'] += 1
            results['errors'].append(f"{txn_data.get('id', '?')}: {str(e)}")

    return jsonify({'success': True, 'results': results}), 200


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

@transactions_bp.route('', methods=['GET'])
@jwt_required()
def list_transactions():
    """List transactions.  Owner sees all; cashier sees only their own."""
    identity = get_jwt_identity()

    query = Transaction.query
    if identity['role'] != 'owner':
        query = query.filter_by(cashier_id=identity['id'])

    shift_id = request.args.get('shiftId')
    date_from = request.args.get('dateFrom')
    date_to = request.args.get('dateTo')

    if shift_id:
        query = query.filter_by(shift_id=shift_id)
    if date_from:
        query = query.filter(Transaction.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Transaction.created_at <= datetime.fromisoformat(date_to))

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    paginated = query.order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'success': True,
        'data': [t.to_dict() for t in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'currentPage': page,
    }), 200


@transactions_bp.route('/<transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    identity = get_jwt_identity()
    txn = Transaction.query.get(transaction_id)
    if not txn:
        return jsonify({'success': False, 'message': 'Transaction not found'}), 404
    if identity['role'] != 'owner' and txn.cashier_id != identity['id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    return jsonify({'success': True, 'data': txn.to_dict()}), 200
