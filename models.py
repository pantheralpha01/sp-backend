from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
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
