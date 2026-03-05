from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# ---------------------------------------------------------------------------
# First-time setup
# ---------------------------------------------------------------------------

@auth_bp.route('/setup/status', methods=['GET'])
def setup_status():
    """Check whether the initial owner account has been created yet."""
    return jsonify({'needsSetup': User.query.count() == 0}), 200


@auth_bp.route('/setup', methods=['POST'])
def initial_setup():
    """Create the first owner account.  Blocked once any user exists."""
    if User.query.count() > 0:
        return jsonify({'success': False, 'message': 'Setup already completed'}), 403

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    pin = str(data.get('pin', ''))

    if not name or not pin:
        return jsonify({'success': False, 'message': 'Name and PIN are required'}), 400
    if not pin.isdigit() or len(pin) < 4 or len(pin) > 6:
        return jsonify({'success': False, 'message': 'PIN must be 4-6 digits'}), 400

    user = User(name=name, role='owner')
    user.set_pin(pin)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(
        identity={'id': user.id, 'name': user.name, 'role': user.role}
    )
    return jsonify({'success': True, 'token': token, 'user': user.to_dict()}), 201


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate with name + PIN, return a JWT."""
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    pin = str(data.get('pin', ''))

    if not name or not pin:
        return jsonify({'success': False, 'message': 'Name and PIN are required'}), 400

    user = User.query.filter(
        db.func.lower(User.name) == name.lower(),
        User.is_active == True
    ).first()

    if not user or not user.check_pin(pin):
        return jsonify({'success': False, 'message': 'Invalid name or PIN'}), 401

    token = create_access_token(
        identity={'id': user.id, 'name': user.name, 'role': user.role}
    )
    return jsonify({'success': True, 'token': token, 'user': user.to_dict()}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Return the profile of the authenticated user."""
    identity = get_jwt_identity()
    user = User.query.get(identity['id'])
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    return jsonify({'success': True, 'user': user.to_dict()}), 200


# ---------------------------------------------------------------------------
# User management (owner only)
# ---------------------------------------------------------------------------

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """List all users.  Owner only."""
    identity = get_jwt_identity()
    if identity['role'] != 'owner':
        return jsonify({'success': False, 'message': 'Owner access required'}), 403

    users = User.query.order_by(User.name).all()
    return jsonify({'success': True, 'data': [u.to_dict() for u in users]}), 200


@auth_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create a new cashier or owner account.  Owner only."""
    identity = get_jwt_identity()
    if identity['role'] != 'owner':
        return jsonify({'success': False, 'message': 'Owner access required'}), 403

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    pin = str(data.get('pin', ''))
    role = data.get('role', 'cashier')

    if not name or not pin:
        return jsonify({'success': False, 'message': 'Name and PIN are required'}), 400
    if not pin.isdigit() or len(pin) < 4 or len(pin) > 6:
        return jsonify({'success': False, 'message': 'PIN must be 4-6 digits'}), 400
    if role not in ('owner', 'cashier'):
        return jsonify({'success': False, 'message': 'Role must be owner or cashier'}), 400

    if User.query.filter(db.func.lower(User.name) == name.lower()).first():
        return jsonify({'success': False, 'message': 'A user with that name already exists'}), 409

    user = User(name=name, role=role)
    user.set_pin(pin)
    db.session.add(user)
    db.session.commit()

    return jsonify({'success': True, 'user': user.to_dict()}), 201


@auth_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update a user.  Owner can change anything; a cashier can only change their own PIN."""
    identity = get_jwt_identity()
    is_owner = identity['role'] == 'owner'
    is_self = identity['id'] == user_id

    if not is_owner and not is_self:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    data = request.get_json() or {}

    if 'pin' in data:
        new_pin = str(data['pin'])
        if not new_pin.isdigit() or len(new_pin) < 4 or len(new_pin) > 6:
            return jsonify({'success': False, 'message': 'PIN must be 4-6 digits'}), 400
        user.set_pin(new_pin)

    if is_owner:
        if 'name' in data:
            user.name = data['name'].strip()
        if 'role' in data and data['role'] in ('owner', 'cashier'):
            user.role = data['role']
        if 'isActive' in data:
            user.is_active = bool(data['isActive'])

    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()}), 200
