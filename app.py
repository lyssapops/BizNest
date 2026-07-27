from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "biznest_secret_key"  

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///biznest.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, nullable=False)

class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    customer = db.relationship("Customer")

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    product = db.relationship("Product")

    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.String(50))

class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    expense_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.String(50))
    category = db.Column(db.String(100))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        print("Email entered:", repr(email))
        print("Password entered:", repr(password))

        user = User.query.filter_by(email=email).first()

        print("User found:", user)

        if user is None:
            return "No user found with that email."

        print("Database password:", repr(user.password))

        if user.password == password:
            return redirect(url_for("dashboard"))
        else:
            return "Password is incorrect."

    return render_template("login.html")
 

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match!"

        user = User(full_name=full_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():

    customer_count = Customer.query.count()
    product_count = Product.query.count()
    sales_count = Sale.query.count()

    total_expenses = db.session.query(
        db.func.sum(Expense.amount)
    ).scalar() or 0

    total_revenue = db.session.query(
        db.func.sum(Sale.total_price)
    ).scalar() or 0


    recent_sales = Sale.query.order_by(
        Sale.id.desc()
    ).limit(5).all()


    top_product = None
    top_quantity = 0


    for product in Product.query.all():

        total_sold = db.session.query(
            db.func.sum(Sale.quantity)
        ).filter(
            Sale.product_id == product.id
        ).scalar() or 0


        if total_sold > top_quantity:
            top_quantity = total_sold
            top_product = product.product_name



    low_stock = Product.query.filter(
        Product.quantity < 5
    ).all()

    customers = Customer.query.all()
    products = Product.query.all()

    customer_lookup = {
        c.id: c.name for c in customers
    }

    product_lookup = {
        p.id: p.product_name for p in products
    }

    # Sales chart data

    sales_data = Sale.query.all()

    sales_dates = [
        str(sale.id)
        for sale in sales_data
    ]

    sales_amounts = [
        float(sale.total_price)
        for sale in sales_data
    ]

    return render_template(
        "dashboard.html",
        customer_count=customer_count,
        product_count=product_count,
        sales_count=sales_count,
        expense_count=total_expenses,
        total_revenue=total_revenue,
        recent_sales=recent_sales,
        customer_lookup=customer_lookup,
        product_lookup=product_lookup,
        low_stock=low_stock,
        top_product=top_product,
        top_quantity=top_quantity,
        sales_dates=sales_dates,
        sales_amounts=sales_amounts
    )

@app.route("/add_customer", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        address = request.form["address"]

        customer = Customer(
            name=name, 
            phone=phone, 
            email=email, 
            address=address
            )
        db.session.add(customer)
        db.session.commit()

        flash("Customer added successfully!", "success")

        return redirect(url_for("customers"))

    return render_template("add_customer.html")

@app.route("/customers")
def customers():

    search = request.args.get("search", "")

    if search:
        customers = Customer.query.filter(
            Customer.name.ilike(f"%{search}%")
        ).all()
    else:
        customers = Customer.query.all()

    return render_template(
        "customers.html",
        customers=customers,
        search=search
    )

@app.route("/delete_customer/<int:id>")
def delete_customer(id):

    customer = Customer.query.get_or_404(id)

    db.session.delete(customer)
    db.session.commit()

    flash("Customer deleted successfully!", "success")

    return redirect(url_for("customers"))

@app.route("/edit_customer/<int:id>", methods=["GET", "POST"])
def edit_customer(id):

    customer = Customer.query.get_or_404(id)

    if request.method == "POST":
        customer.name = request.form["name"]
        customer.phone = request.form["phone"]
        customer.email = request.form["email"]
        customer.address = request.form["address"]

        db.session.commit()

        return redirect(url_for("customers"))

    return render_template("edit_customer.html", customer=customer)

@app.route("/add_product", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":

        product = Product(
            product_name=request.form["product_name"],
            category=request.form["category"],
            quantity=request.form["quantity"],
            price=request.form["price"]
        )

        db.session.add(product)
        db.session.commit()

        flash("Product added successfully!", "success")

        return redirect(url_for("inventory"))

    return render_template("add_product.html")

@app.route("/inventory")
def inventory():

    products = Product.query.all()

    return render_template(
        "inventory.html",
        products=products
    )

@app.route("/edit_product/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    product = Product.query.get_or_404(id)

    if request.method == "POST":

        product.product_name = request.form["product_name"]
        product.category = request.form["category"]
        product.quantity = request.form["quantity"]
        product.price = request.form["price"]

        db.session.commit()

        flash("Product updated successfully!", "success")

        return redirect(url_for("inventory"))

    return render_template("edit_product.html", product=product)

@app.route("/delete_product/<int:id>")
def delete_product(id):

    product = Product.query.get_or_404(id)

    existing_sale = Sale.query.filter_by(product_id=product.id).first()

    if existing_sale:
        flash("This product cannot be deleted because it has sales history.", "error")
        return redirect(url_for("inventory"))

    db.session.delete(product)
    db.session.commit()

    flash("Product deleted successfully!", "success")

    return redirect(url_for("inventory"))

@app.route("/sales", methods=["GET", "POST"])
def sales():

    customers = Customer.query.all()
    products = Product.query.all()

    if request.method == "POST":

        customer_id = int(request.form["customer_id"])
        product_id = int(request.form["product_id"])
        quantity = int(request.form["quantity"])

        product = Product.query.get(product_id)

        if quantity > product.quantity:
            return "Not enough stock available." 

        total = quantity * product.price

        sale = Sale(
            customer_id=customer_id,
            product_id=product_id,
            quantity=quantity,
            total_price=total,
            sale_date=datetime.now().strftime("%d/%m/%Y %H:%M")
        )

        db.session.add(sale)

        product.quantity -= quantity

        db.session.commit()

        flash("Sale recorded successfully!", "success")

        return redirect(url_for("sales"))

    sales = Sale.query.all()

    customer_lookup = {customer.id: customer.name for customer in customers}
    product_lookup = {product.id: product.product_name for product in products}

    return render_template(
        "sales.html",
        customers=customers,
        products=products,
        sales=sales,
        customer_lookup=customer_lookup,
        product_lookup=product_lookup
    )

@app.route("/delete_sale/<int:id>")
def delete_sale(id):

    sale = Sale.query.get_or_404(id)

    product = Product.query.get(sale.product_id)

    # Only restore stock if the product still exists
    if product:
        product.quantity += sale.quantity

    db.session.delete(sale)

    db.session.commit()

    flash("Sale deleted successfully!", "success")

    return redirect(url_for("sales"))

@app.route("/expenses")
def expenses():

    expenses = Expense.query.all()

    return render_template(
        "expenses.html",
        expenses=expenses
    )

@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():

    if request.method == "POST":

        expense = Expense(
            expense_name=request.form["expense_name"],
            amount=float(request.form["amount"]),
            expense_date=request.form["expense_date"],
            category=request.form["category"]
        )

        db.session.add(expense)
        db.session.commit()

        return redirect(url_for("expenses"))

        flash("Expense added successfully!", "success")

    return render_template("add_expense.html")

@app.route("/edit_expense/<int:id>", methods=["GET", "POST"])
def edit_expense(id):

    expense = Expense.query.get_or_404(id)

    if request.method == "POST":

        expense.expense_name = request.form["expense_name"]
        expense.amount = float(request.form["amount"])
        expense.expense_date = request.form["expense_date"]
        expense.category = request.form["category"]

        db.session.commit()

        return redirect(url_for("expenses"))

    flash("Expense updated successfully!", "success")

    return render_template("edit_expense.html", expense=expense)


@app.route("/delete_expense/<int:id>")
def delete_expense(id):

    expense = Expense.query.get_or_404(id)

    db.session.delete(expense)
    db.session.commit()

    flash("Expense deleted successfully!", "success")

    return redirect(url_for("expenses"))

@app.route("/reports")
def reports():

    total_customers = Customer.query.count()

    total_products = Product.query.count()

    total_sales = db.session.query(db.func.sum(Sale.total_price)).scalar() or 0

    total_expenses = db.session.query(db.func.sum(Expense.amount)).scalar() or 0

    profit = total_sales - total_expenses

    best_product = (
        db.session.query(
            Product.product_name,
            db.func.sum(Sale.quantity).label("qty")
        )
        .join(Sale, Product.id == Sale.product_id)
        .group_by(Product.product_name)
        .order_by(db.func.sum(Sale.quantity).desc())
        .first()
    )

    if best_product:
        best_product_name = best_product[0]
        best_product_qty = best_product[1]
    else:
        best_product_name = "No sales yet"
        best_product_qty = 0

    low_stock = Product.query.filter(Product.quantity < 5).count()

    return render_template(
        "reports.html",
        total_customers=total_customers,
        total_products=total_products,
        total_sales=total_sales,
        total_expenses=total_expenses,
        profit=profit,
        best_product_name=best_product_name,
        best_product_qty=best_product_qty,
        low_stock=low_stock
    )

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/logout")
def logout():
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
    app.run(debug=True) 