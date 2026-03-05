from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class Product(db.Model):
    """Product model for SQLAlchemy"""
    __tablename__ = 'products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default='')
    category = db.Column(db.String(100), default='General')
    
    # Pricing
    costPrice = db.Column(db.Float, default=0.0)
    sellingPrice = db.Column(db.Float, nullable=False)
    
    # Inventory
    stockLevel = db.Column(db.Integer, default=0)
    reorderLevel = db.Column(db.Integer, default=10)
    
    # Metadata
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert product to dictionary for JSON response"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'costPrice': self.costPrice,
            'sellingPrice': self.sellingPrice,
            'stockLevel': self.stockLevel,
            'reorderLevel': self.reorderLevel,
            'createdAt': self.createdAt.isoformat(),
            'updatedAt': self.updatedAt.isoformat(),
        }
    
    def __repr__(self):
        return f'<Product {self.name} ({self.code})>'


class User(db.Model):
    """Cashier / Owner account"""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, unique=True)
    pin_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='cashier')   # 'owner' or 'cashier'
    is_active = db.Column(db.Boolean, default=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    shifts = db.relationship('Shift', backref='cashier', lazy=True)

    def set_pin(self, pin):
        self.pin_hash = generate_password_hash(str(pin))

    def check_pin(self, pin):
        return check_password_hash(self.pin_hash, str(pin))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'isActive': self.is_active,
            'createdAt': self.createdAt.isoformat(),
        }

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


class Shift(db.Model):
    """A cashier's work session — from opening float to cash reconciliation"""
    __tablename__ = 'shifts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cashier_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    cashier_name = db.Column(db.String(100), nullable=False)
    opening_float = db.Column(db.Float, default=0.0)
    closing_cash = db.Column(db.Float, nullable=True)
    expected_cash = db.Column(db.Float, nullable=True)
    variance = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='open')    # 'open' or 'closed'
    notes = db.Column(db.Text, default='')
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)

    transactions = db.relationship('Transaction', backref='shift', lazy=True)
    expenses = db.relationship('Expense', backref='shift', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'cashierId': self.cashier_id,
            'cashierName': self.cashier_name,
            'openingFloat': self.opening_float,
            'closingCash': self.closing_cash,
            'expectedCash': self.expected_cash,
            'variance': self.variance,
            'status': self.status,
            'notes': self.notes,
            'openedAt': self.opened_at.isoformat(),
            'closedAt': self.closed_at.isoformat() if self.closed_at else None,
        }

    def __repr__(self):
        return f'<Shift {self.cashier_name} {self.status}>'


class Transaction(db.Model):
    """A completed sale — synced from Flutter, immutable once stored"""
    __tablename__ = 'transactions'

    id = db.Column(db.String(36), primary_key=True)   # UUID from Flutter (idempotent)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    shift_id = db.Column(db.String(36), db.ForeignKey('shifts.id'), nullable=True)
    cashier_id = db.Column(db.String(36), nullable=False)
    cashier_name = db.Column(db.String(100), nullable=False)
    subtotal = db.Column(db.Float, default=0.0)
    discount_total = db.Column(db.Float, default=0.0)
    tax_total = db.Column(db.Float, default=0.0)
    grand_total = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='cash')
    is_split_bill = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='completed')   # 'completed' or 'voided'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('TransactionItem', backref='transaction', lazy=True,
                            cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='transaction', lazy=True,
                               cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'receiptNumber': self.receipt_number,
            'shiftId': self.shift_id,
            'cashierId': self.cashier_id,
            'cashierName': self.cashier_name,
            'subtotal': self.subtotal,
            'discountTotal': self.discount_total,
            'taxTotal': self.tax_total,
            'grandTotal': self.grand_total,
            'paymentMethod': self.payment_method,
            'isSplitBill': self.is_split_bill,
            'status': self.status,
            'items': [item.to_dict() for item in self.items],
            'payments': [p.to_dict() for p in self.payments],
            'createdAt': self.created_at.isoformat(),
            'syncedAt': self.synced_at.isoformat(),
        }

    def __repr__(self):
        return f'<Transaction {self.receipt_number}>'


class TransactionItem(db.Model):
    """A single line item within a transaction — price is snapshotted at time of sale"""
    __tablename__ = 'transaction_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = db.Column(db.String(36), db.ForeignKey('transactions.id'), nullable=False)
    product_id = db.Column(db.String(36), nullable=True)
    product_code = db.Column(db.String(50), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)   # snapshotted
    discount = db.Column(db.Float, default=0.0)
    line_total = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'transactionId': self.transaction_id,
            'productId': self.product_id,
            'productCode': self.product_code,
            'productName': self.product_name,
            'quantity': self.quantity,
            'unitPrice': self.unit_price,
            'discount': self.discount,
            'lineTotal': self.line_total,
        }


class Payment(db.Model):
    """One payment leg — multiple per transaction when split bill"""
    __tablename__ = 'payments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = db.Column(db.String(36), db.ForeignKey('transactions.id'), nullable=False)
    method = db.Column(db.String(50), nullable=False)   # cash, mpesa, card
    amount = db.Column(db.Float, nullable=False)
    reference = db.Column(db.String(100), default='')
    phone_number = db.Column(db.String(20), default='')
    card_last4 = db.Column(db.String(4), default='')

    def to_dict(self):
        return {
            'id': self.id,
            'transactionId': self.transaction_id,
            'method': self.method,
            'amount': self.amount,
            'reference': self.reference,
            'phoneNumber': self.phone_number,
            'cardLast4': self.card_last4,
        }


class Expense(db.Model):
    """Cash paid out from the till during a shift"""
    __tablename__ = 'expenses'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shift_id = db.Column(db.String(36), db.ForeignKey('shifts.id'), nullable=True)
    cashier_id = db.Column(db.String(36), nullable=False)
    cashier_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, default='')
    payment_method = db.Column(db.String(50), default='cash')
    approval_status = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    approved_by = db.Column(db.String(100), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'shiftId': self.shift_id,
            'cashierId': self.cashier_id,
            'cashierName': self.cashier_name,
            'category': self.category,
            'amount': self.amount,
            'description': self.description,
            'paymentMethod': self.payment_method,
            'approvalStatus': self.approval_status,
            'approvedBy': self.approved_by,
            'createdAt': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Expense {self.category} {self.amount}>'
