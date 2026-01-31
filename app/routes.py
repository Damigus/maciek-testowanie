"""API routes for the order management system."""
from flask import Blueprint, request, jsonify
from app.services import ProductService, OrderService

api_bp = Blueprint('api', __name__)


# Health check
@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


# Product endpoints
@api_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products."""
    products = ProductService.get_all_products()
    return jsonify([p.to_dict() for p in products]), 200


@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product."""
    product = ProductService.get_product(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product.to_dict()), 200


@api_bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        product = ProductService.create_product(
            name=data.get('name'),
            price=data.get('price', 0),
            stock=data.get('stock', 0)
        )
        return jsonify(product.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/products/<int:product_id>/stock', methods=['PATCH'])
def update_product_stock(product_id):
    """Update product stock."""
    data = request.get_json()
    if not data or 'quantity_change' not in data:
        return jsonify({'error': 'quantity_change is required'}), 400
    
    try:
        product = ProductService.update_stock(product_id, data['quantity_change'])
        return jsonify(product.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# Order endpoints
@api_bp.route('/orders', methods=['GET'])
def get_orders():
    """Get all orders, optionally filtered by status."""
    status = request.args.get('status')
    if status:
        orders = OrderService.get_orders_by_status(status)
    else:
        orders = OrderService.get_all_orders()
    return jsonify([o.to_dict() for o in orders]), 200


@api_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get a specific order."""
    order = OrderService.get_order(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify(order.to_dict()), 200


@api_bp.route('/orders', methods=['POST'])
def create_order():
    """Create a new order."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        order = OrderService.create_order(
            customer_name=data.get('customer_name'),
            customer_email=data.get('customer_email'),
            items=data.get('items', [])
        )
        return jsonify(order.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/orders/<int:order_id>/confirm', methods=['POST'])
def confirm_order(order_id):
    """Confirm a pending order."""
    try:
        order = OrderService.confirm_order(order_id)
        return jsonify(order.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel a pending order."""
    try:
        order = OrderService.cancel_order(order_id)
        return jsonify(order.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/orders/<int:order_id>/complete', methods=['POST'])
def complete_order(order_id):
    """Mark an order as completed."""
    try:
        order = OrderService.complete_order(order_id)
        return jsonify(order.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
