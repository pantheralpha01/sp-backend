"""
eTIMS / KRA Integration Routes
------------------------------
Owner-only settings & device registration:
  GET  /api/owner/etims/settings
  POST /api/owner/etims/settings
  POST /api/owner/etims/devices/register
  GET  /api/owner/etims/invoices
  POST /api/owner/etims/invoices/retry

Cashier-accessible (submit before printing):
  POST /api/etims/invoices/submit
"""

import os
import hashlib
import base64
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models import EtimsConfig, EtimsInvoiceLog, Transaction, db

etims_bp = Blueprint('etims', __name__)


# ---------------------------------------------------------------------------
# Encryption helpers (Fernet derived from JWT_SECRET_KEY)
# ---------------------------------------------------------------------------

def _get_fernet():
    from cryptography.fernet import Fernet
    secret = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def _encrypt(value: str) -> str:
    if not value:
        return ''
    return _get_fernet().encrypt(value.encode()).decode()


def _decrypt(value: str) -> str:
    if not value:
        return ''
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except Exception:
        return ''


def _get_or_create_config() -> EtimsConfig:
    cfg = EtimsConfig.query.first()
    if not cfg:
        cfg = EtimsConfig()
        db.session.add(cfg)
        db.session.commit()
    return cfg


def _require_owner():
    claims = get_jwt()
    if claims.get('role') != 'owner':
        return jsonify({'success': False, 'message': 'Owner access required'}), 403
    return None


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@etims_bp.route('/api/owner/etims/settings', methods=['GET'])
@jwt_required()
def get_etims_settings():
    err = _require_owner()
    if err:
        return err
    cfg = _get_or_create_config()
    return jsonify({'success': True, 'data': cfg.to_dict()}), 200


@etims_bp.route('/api/owner/etims/settings', methods=['POST'])
@jwt_required()
def save_etims_settings():
    err = _require_owner()
    if err:
        return err
    cfg = _get_or_create_config()
    data = request.get_json() or {}

    if 'kraPin' in data:
        cfg.kra_pin = data['kraPin'].strip()
    if 'businessName' in data:
        cfg.business_name = data['businessName'].strip()
    if 'branchId' in data:
        cfg.branch_id = data['branchId'].strip()
    if 'deviceSerial' in data:
        cfg.device_serial = data['deviceSerial'].strip()
    if 'environment' in data and data['environment'] in ('sandbox', 'production'):
        cfg.environment = data['environment']
    if 'mode' in data and data['mode'] in ('disabled', 'optional', 'strict'):
        cfg.mode = data['mode']
    # Only update credentials if new values are provided
    if 'clientId' in data and data['clientId'].strip():
        cfg.client_id_encrypted = _encrypt(data['clientId'].strip())
    if 'clientSecret' in data and data['clientSecret'].strip():
        cfg.client_secret_encrypted = _encrypt(data['clientSecret'].strip())

    cfg.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'data': cfg.to_dict()}), 200


# ---------------------------------------------------------------------------
# Device registration
# ---------------------------------------------------------------------------

@etims_bp.route('/api/owner/etims/devices/register', methods=['POST'])
@jwt_required()
def register_device():
    err = _require_owner()
    if err:
        return err
    cfg = _get_or_create_config()

    if not cfg.client_id_encrypted or not cfg.kra_pin:
        return jsonify({
            'success': False,
            'message': 'KRA credentials not configured. Save settings first.'
        }), 400

    client_id = _decrypt(cfg.client_id_encrypted)
    client_secret = _decrypt(cfg.client_secret_encrypted)
    base_url = _get_base_url(cfg.environment)

    try:
        token = _get_kra_token(base_url, client_id, client_secret)
        payload = {
            'taxpayerPin': cfg.kra_pin,
            'branchId': cfg.branch_id,
            'deviceSerialNo': cfg.device_serial,
            'deviceName': 'SalesPro POS',
        }
        resp = requests.post(
            f'{base_url}/api/devices',
            json=payload,
            headers={'Authorization': f'Bearer {token}'},
            timeout=15
        )
        kra_data = resp.json()

        if kra_data.get('status') == 'REGISTERED' or kra_data.get('deviceId'):
            cfg.device_id = kra_data.get('deviceId', '')
            cfg.device_registered = True
            db.session.commit()
            return jsonify({'success': True, 'data': cfg.to_dict(), 'kraResponse': kra_data}), 200
        else:
            return jsonify({
                'success': False,
                'message': 'KRA rejected device registration',
                'kraResponse': kra_data
            }), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# Invoice submission (cashier or owner calls this before printing)
# ---------------------------------------------------------------------------

@etims_bp.route('/api/etims/invoices/submit', methods=['POST'])
@jwt_required()
def submit_invoice():
    """
    Body: { "transactionId": "txn-xxx" }
    Returns eTIMS invoice number + base64 QR on success.
    If mode is 'optional' and KRA is unreachable, returns { queued: true }.
    """
    data = request.get_json() or {}
    txn_id = data.get('transactionId', '').strip()
    if not txn_id:
        return jsonify({'success': False, 'message': 'transactionId is required'}), 400

    cfg = _get_or_create_config()

    if cfg.mode == 'disabled':
        return jsonify({'success': False, 'message': 'eTIMS is disabled for this business'}), 400

    # Idempotency: already approved — return existing log
    existing = EtimsInvoiceLog.query.filter_by(
        transaction_id=txn_id, etims_status='approved'
    ).first()
    if existing:
        return jsonify({'success': True, 'data': existing.to_dict()}), 200

    txn = Transaction.query.get(txn_id)
    if not txn:
        return jsonify({'success': False, 'message': 'Transaction not found'}), 404

    # Create log entry if it doesn't exist
    log = EtimsInvoiceLog.query.filter_by(transaction_id=txn_id).first()
    if not log:
        log = EtimsInvoiceLog(
            transaction_id=txn_id,
            receipt_number=txn.receipt_number,
            etims_status='queued',
        )
        db.session.add(log)
        db.session.commit()

    if not cfg.client_id_encrypted or not cfg.kra_pin:
        log.etims_status = 'failed'
        log.error_message = 'eTIMS credentials not configured'
        db.session.commit()
        if cfg.mode == 'optional':
            return jsonify({
                'success': False,
                'queued': True,
                'message': 'eTIMS not configured; invoice queued'
            }), 200
        return jsonify({'success': False, 'message': 'eTIMS not configured'}), 400

    client_id = _decrypt(cfg.client_id_encrypted)
    client_secret = _decrypt(cfg.client_secret_encrypted)
    base_url = _get_base_url(cfg.environment)

    try:
        token = _get_kra_token(base_url, client_id, client_secret)
        invoice_payload = _build_invoice_payload(cfg, txn)
        resp = requests.post(
            f'{base_url}/api/invoices',
            json=invoice_payload,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            timeout=15
        )
        kra_data = resp.json()

        if kra_data.get('status') == 'SUCCESS':
            log.etims_status = 'approved'
            log.etims_invoice_number = kra_data.get('invoiceNumber', '')
            log.qr_data = kra_data.get('qrCode', '')
            log.signature = kra_data.get('signature', '')
            log.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'data': log.to_dict()}), 200
        else:
            log.etims_status = 'failed'
            log.error_message = str(kra_data)
            log.retries += 1
            db.session.commit()
            if cfg.mode == 'optional':
                return jsonify({
                    'success': False,
                    'queued': True,
                    'message': 'KRA submission failed; invoice queued for retry',
                    'kraResponse': kra_data
                }), 200
            return jsonify({
                'success': False,
                'message': 'KRA submission failed',
                'kraResponse': kra_data
            }), 400

    except Exception as e:
        log.etims_status = 'failed'
        log.error_message = str(e)
        log.retries += 1
        db.session.commit()
        if cfg.mode == 'optional':
            return jsonify({
                'success': False,
                'queued': True,
                'message': 'Could not reach KRA; invoice queued for retry'
            }), 200
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ---------------------------------------------------------------------------
# Invoice log (owner view)
# ---------------------------------------------------------------------------

@etims_bp.route('/api/owner/etims/invoices', methods=['GET'])
@jwt_required()
def list_etims_invoices():
    err = _require_owner()
    if err:
        return err
    status_filter = request.args.get('status')
    query = EtimsInvoiceLog.query
    if status_filter:
        query = query.filter_by(etims_status=status_filter)
    logs = query.order_by(EtimsInvoiceLog.created_at.desc()).limit(200).all()
    return jsonify({'success': True, 'data': [lg.to_dict() for lg in logs]}), 200


# ---------------------------------------------------------------------------
# Retry failed / queued invoices
# ---------------------------------------------------------------------------

@etims_bp.route('/api/owner/etims/invoices/retry', methods=['POST'])
@jwt_required()
def retry_failed_invoices():
    err = _require_owner()
    if err:
        return err
    cfg = _get_or_create_config()
    if not cfg.client_id_encrypted:
        return jsonify({'success': False, 'message': 'eTIMS not configured'}), 400

    pending = EtimsInvoiceLog.query.filter(
        EtimsInvoiceLog.etims_status.in_(['failed', 'queued']),
        EtimsInvoiceLog.retries < 5
    ).all()

    client_id = _decrypt(cfg.client_id_encrypted)
    client_secret = _decrypt(cfg.client_secret_encrypted)
    base_url = _get_base_url(cfg.environment)

    try:
        token = _get_kra_token(base_url, client_id, client_secret)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Cannot get KRA token: {e}'}), 500

    retried = 0
    approved = 0
    errors = []

    for log in pending:
        txn = Transaction.query.get(log.transaction_id)
        if not txn:
            continue
        try:
            invoice_payload = _build_invoice_payload(cfg, txn)
            resp = requests.post(
                f'{base_url}/api/invoices',
                json=invoice_payload,
                headers={'Authorization': f'Bearer {token}'},
                timeout=15
            )
            kra_data = resp.json()
            retried += 1
            if kra_data.get('status') == 'SUCCESS':
                log.etims_status = 'approved'
                log.etims_invoice_number = kra_data.get('invoiceNumber', '')
                log.qr_data = kra_data.get('qrCode', '')
                log.signature = kra_data.get('signature', '')
                approved += 1
            else:
                log.retries += 1
                log.error_message = str(kra_data)
            log.updated_at = datetime.utcnow()
        except Exception as e:
            log.retries += 1
            log.error_message = str(e)
            errors.append(str(e))

    db.session.commit()
    return jsonify({
        'success': True,
        'retried': retried,
        'approved': approved,
        'errors': errors
    }), 200


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_base_url(environment: str) -> str:
    if environment == 'production':
        return os.environ.get('ETIMS_PROD_URL', 'https://etims-api.kra.go.ke')
    return os.environ.get('ETIMS_SANDBOX_URL', 'https://etims-sandbox.kra.go.ke')


def _get_kra_token(base_url: str, client_id: str, client_secret: str) -> str:
    resp = requests.post(
        f'{base_url}/oauth/token',
        json={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
        },
        timeout=15
    )
    token_data = resp.json()
    token = token_data.get('access_token')
    if not token:
        raise ValueError(f'No access_token in KRA response: {token_data}')
    return token


def _build_invoice_payload(cfg: EtimsConfig, txn: Transaction) -> dict:
    items = []
    for item in txn.items:
        vat_rate = 16.0
        items.append({
            'itemCode': item.product_code,
            'itemName': item.product_name,
            'quantity': item.quantity,
            'unitPrice': item.unit_price,
            'vatRate': vat_rate,
            'totalAmount': item.line_total,
        })
    return {
        'deviceId': cfg.device_id,
        'invoiceNo': txn.receipt_number,
        'saleDate': txn.created_at.isoformat(),
        'buyerPin': '',
        'items': items,
        'totalAmount': txn.subtotal,
        'vatAmount': txn.tax_total,
        'grandTotal': txn.grand_total,
    }
