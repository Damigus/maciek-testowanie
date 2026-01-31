"""Business logic services for the order management system."""
from app.models import db, Product, Order, OrderItem


class ProductService:
    """Service for product-related business operations."""
    
    @staticmethod
    def create_product(name, price, stock=0):
        """Create a new product with validation."""
        if not name or not name.strip():
            raise ValueError("Product name is required")
        if price <= 0:
            raise ValueError("Price must be greater than zero")
        if stock < 0:
            raise ValueError("Stock cannot be negative")
        
        product = Product(name=name.strip(), price=price, stock=stock)
        db.session.add(product)
        db.session.commit()
        return product
    
    @staticmethod
    def update_stock(product_id, quantity_change):
        """Update product stock. Positive = add, negative = subtract."""
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Product not found")
        
        new_stock = product.stock + quantity_change
        if new_stock < 0:
            raise ValueError("Insufficient stock")
        
        product.stock = new_stock
        db.session.commit()
        return product
    
    @staticmethod
    def get_all_products():
        """Get all products."""
        return Product.query.all()
    
    @staticmethod
    def get_product(product_id):
        """Get product by ID."""
        return Product.query.get(product_id)


class OrderService:
    """Service for order-related business operations."""
    
    @staticmethod
    def create_order(customer_name, customer_email, items):
        """
        Create a new order with items.
        
        Args:
            customer_name: Customer's name
            customer_email: Customer's email
            items: List of dicts with 'product_id' and 'quantity'
        
        Returns:
            Created order
            
        Raises:
            ValueError: If validation fails
        """
        if not customer_name or not customer_name.strip():
            raise ValueError("Customer name is required")
        if not customer_email or '@' not in customer_email:
            raise ValueError("Valid customer email is required")
        if not items:
            raise ValueError("Order must contain at least one item")
        
        order = Order(
            customer_name=customer_name.strip(),
            customer_email=customer_email.strip()
        )
        db.session.add(order)
        
        for item_data in items:
            product = Product.query.get(item_data['product_id'])
            if not product:
                db.session.rollback()
                raise ValueError(f"Product {item_data['product_id']} not found")
            
            quantity = item_data['quantity']
            if quantity <= 0:
                db.session.rollback()
                raise ValueError("Quantity must be positive")
            
            if not product.is_available(quantity):
                db.session.rollback()
                raise ValueError(f"Insufficient stock for product {product.name}")
            
            # Reserve stock
            product.stock -= quantity
            
            order_item = OrderItem(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
                subtotal=product.price * quantity
            )
            db.session.add(order_item)
        
        order.calculate_total()
        db.session.commit()
        return order
    
    @staticmethod
    def confirm_order(order_id):
        """Confirm a pending order."""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")
        if order.status != Order.STATUS_PENDING:
            raise ValueError("Only pending orders can be confirmed")
        
        order.status = Order.STATUS_CONFIRMED
        db.session.commit()
        return order
    
    @staticmethod
    def cancel_order(order_id):
        """Cancel an order and restore stock."""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")
        if not order.can_be_cancelled():
            raise ValueError("Only pending orders can be cancelled")
        
        # Restore stock for all items
        for item in order.items:
            item.product.stock += item.quantity
        
        order.status = Order.STATUS_CANCELLED
        db.session.commit()
        return order
    
    @staticmethod
    def complete_order(order_id):
        """Mark order as completed (delivered)."""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")
        if not order.can_be_completed():
            raise ValueError("Only confirmed orders can be completed")
        
        order.status = Order.STATUS_COMPLETED
        db.session.commit()
        return order
    
    @staticmethod
    def get_order(order_id):
        """Get order by ID."""
        return Order.query.get(order_id)
    
    @staticmethod
    def get_all_orders():
        """Get all orders."""
        return Order.query.all()
    
    @staticmethod
    def get_orders_by_status(status):
        """Get orders filtered by status."""
        return Order.query.filter_by(status=status).all()
