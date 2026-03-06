from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import Expense, db
from datetime import datetime

expenses_bp = Blueprint('expenses', __name__, url_prefix='/api/expenses')


@expenses_bp.route('', methods=['POST'])
@jwt_required()
def sync_expense():
    """Receive a synced expense from Flutter.  Idempotent on expense id."""
    user_id = get_jwt_identity()
    claims = get_jwt()
    data = request.get_json() or {}

    if not data.get('category') or 'amount' not in data:
        return jsonify({'success': False, 'message': 'category and amount are required'}), 400

    # Idempotency
    if data.get('id'):
        existing = Expense.query.get(data['id'])
        if existing:
            return jsonify({'success': True, 'message': 'Already synced', 'data': existing.to_dict()}), 200

    try:
        expense = Expense(
            id=data.get('id'),   # None → auto-generated UUID
            shift_id=data.get('shiftId'),
            cashier_id=data.get('cashierId', user_id),
            cashier_name=data.get('cashierName', claims.get('name', '')),

            category=data['category'],
            amount=float(data['amount']),
            description=data.get('description', ''),
            payment_method=data.get('paymentMethod', 'cash'),
            approval_status=data.get('approvalStatus', 'pending'),
            created_at=(
                datetime.fromisoformat(data['createdAt'])
                if data.get('createdAt') else datetime.utcnow()
            ),
        )
        db.session.add(expense)
        db.session.commit()
        return jsonify({'success': True, 'data': expense.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@expenses_bp.route('', methods=['GET'])
@jwt_required()
def list_expenses():
    """List expenses.  Owner sees all; cashier sees only their own."""
    user_id = get_jwt_identity()
    claims = get_jwt()

    query = Expense.query
    if claims.get('role') != 'owner':
        query = query.filter_by(cashier_id=user_id)

    shift_id = request.args.get('shiftId')
    status = request.args.get('status')
    if shift_id:
        query = query.filter_by(shift_id=shift_id)
    if status:
        query = query.filter_by(approval_status=status)

    expenses = query.order_by(Expense.created_at.desc()).limit(200).all()
    return jsonify({'success': True, 'data': [e.to_dict() for e in expenses]}), 200


@expenses_bp.route('/<expense_id>/approve', methods=['PUT'])
@jwt_required()
def approve_expense(expense_id):
    claims = get_jwt()
    if claims.get('role') != 'owner':
        return jsonify({'success': False, 'message': 'Owner access required'}), 403

    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({'success': False, 'message': 'Expense not found'}), 404

    expense.approval_status = 'approved'
    expense.approved_by = claims.get('name', '')
    db.session.commit()
    return jsonify({'success': True, 'data': expense.to_dict()}), 200


@expenses_bp.route('/<expense_id>/reject', methods=['PUT'])
@jwt_required()
def reject_expense(expense_id):
    claims = get_jwt()
    if claims.get('role') != 'owner':
        return jsonify({'success': False, 'message': 'Owner access required'}), 403

    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({'success': False, 'message': 'Expense not found'}), 404

    expense.approval_status = 'rejected'
    expense.approved_by = claims.get('name', '')
    db.session.commit()
    return jsonify({'success': True, 'data': expense.to_dict()}), 200
