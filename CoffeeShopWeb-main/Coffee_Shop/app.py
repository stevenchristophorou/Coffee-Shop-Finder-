import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from dotenv import load_dotenv

from sqlalchemy import text 

load_dotenv()

app = Flask(__name__)
# Config from env
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret')
SQL_USER = os.getenv('SQL_USER', 'root')
SQL_PASSWORD = os.getenv('SQL_PASSWORD', '')
SQL_HOST = os.getenv('SQL_HOST', '127.0.0.1')
SQL_PORT = os.getenv('SQL_PORT', '3306')
SQL_DB = os.getenv('SQL_DB', 'coffeeshop')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{SQL_DB}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Turn the database models into classes
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum('user','admin','manager', name='role_enum'), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviews = db.relationship('Review', backref='user', cascade='all, delete-orphan')

class Shop(db.Model):
    __tablename__ = 'shops'
    shop_id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    phone_num = db.Column(db.String(30))
    website = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    locations = db.relationship('Location', backref='shop', cascade='all, delete-orphan')
    menu_items = db.relationship('MenuItem', backref='shop', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='shop', cascade='all, delete-orphan')

class Location(db.Model):
    __tablename__ = 'locations'
    location_id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.shop_id', ondelete='CASCADE'), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    zipcode = db.Column(db.String(30))
    

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    item_id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.shop_id', ondelete='CASCADE'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10,2), nullable=False)
    category = db.Column(db.Enum('coffee','food','pastry','other', name='category_enum'))

class Review(db.Model):
    __tablename__ = 'reviews'
    review_id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.shop_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    rating = db.Column(db.Integer)
    review_text = db.Column(db.Text)
    review_date = db.Column(db.DateTime, default=datetime.utcnow)


# Function to require specific roles for endpoints
def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            if not user or user.role not in roles:
                return jsonify({"Error": "Incorrect permissions"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# ----------------------
# Routes for HTML pages
# ----------------------
# Home page
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/login.html')
def login_page():
    return render_template("Login.html")

@app.route('/signup.html')
def signup_page():
    return render_template("SignUp.html")

@app.route('/learnmore.html')
def learn_more_page():
    return render_template("LearnMore.html")

@app.route("/menu.html")
def menu_page():
    return render_template("menu.html")

@app.route("/reviews.html")
def reviews_page():
    return render_template("reviews.html")


# ----------------------
# Register a new user
# ----------------------
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    

    if not username or not email or not password:
        return jsonify({"Error": "username, email, password required"}), 400
    if User.query.filter((User.username==username)|(User.email==email)).first():
        return jsonify({"Error": "username or email already exists"}), 409

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, email=email, password=hashed_pw, role=role)

    db.session.add(user)
    db.session.commit()
    return jsonify({"Success": "User created successfully"}), 201
 

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.form
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"Error": "username & password required"}), 400
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"Error": "Bad username or password"}), 401
    access_token = create_access_token(identity=str(user.user_id), expires_delta=timedelta(days=7))
    return jsonify({
        "access_token": access_token,
        "username": username,
        "role": user.role
    }), 200

@app.route("/user.html")
def user_page():
    return render_template("user.html")

@app.route("/manager.html")
def manager_page():
    return render_template("manager.html")

@app.route("/admin.html")
def admin_page():
    return render_template("admin.html")

# ----------------------
# Shops endpoints
# ----------------------
@app.route('/shops', methods=['GET'])
def list_shops():
    q_city = request.args.get('city')
    q_state = request.args.get('state')
    q_name = request.args.get('name')

    query = Shop.query
    if q_name:
        query = query.filter(Shop.shop_name.ilike(f"%{q_name}%"))
    if q_city or q_state:
        query = query.join(Location)
        if q_city:
            query = query.filter(Location.city.ilike(f"%{q_city}%"))
        if q_state:
            query = query.filter(Location.state.ilike(f"%{q_state}%"))
    

    shops = query.all()
    out = []
    for s in shops:
        out.append({
            "shop_id": s.shop_id,
            "shop_name": s.shop_name,
            "description": s.description,
            "phone_num": s.phone_num,
            "website": s.website,
            "created_at": s.created_at.isoformat()
        })
    return jsonify(out)

@app.route('/shops', methods=['POST'])
@role_required('manager','admin')
def create_shop():
    data = request.get_json() or {}
    name = data.get('shop_name')
    if not name:
        return jsonify({"Error": "Shop name required"}), 400
    
    s = Shop(shop_name=name, description=data.get('description'), phone_num=data.get('phone_num'), website=data.get('website'))
    db.session.add(s)
    db.session.commit()

    return jsonify({"Success": "Shop successfully created", "shop_id": s.shop_id}), 201

@app.route('/shops/<int:shop_id>', methods=['GET'])
def get_shop(shop_id):
    s = Shop.query.get_or_404(shop_id)

    locations = [{
        "location_id": l.location_id, "address": l.address, "city": l.city, "state": l.state,"zipcode": l.zipcode
    } for l in s.locations]
    menu = [{
        "item_id": it.item_id, "item_name": it.item_name, "price": str(it.price), "category": it.category, "description": it.description,
    } for it in s.menu_items]
    reviews = [{
        "review_id": r.review_id, "user_id": r.user_id, "rating": r.rating, "text": r.review_text, "date": r.review_date.isoformat()
    } for r in s.reviews]

    return jsonify({
        "shop_id": s.shop_id, "shop_name": s.shop_name, "description": s.description,
        "phone_num": s.phone_num, "website": s.website,
        "locations": locations, "menu_items": menu, "reviews": reviews
    })

@app.route('/shops/<int:shop_id>', methods=['PUT'])
@role_required('manager','admin')
def update_shop(shop_id):
    s = Shop.query.get_or_404(shop_id)
    data = request.get_json() or {}
    s.shop_name = data.get('shop_name', s.shop_name)
    s.description = data.get('description', s.description)
    s.phone_num = data.get('phone_num', s.phone_num)
    s.website = data.get('website', s.website)
    db.session.commit()
    return jsonify({"Success": "Successfully updated"})

# ----------------------
# Locations
# ----------------------
@app.route('/shops/<int:shop_id>/locations', methods=['POST'])
@role_required('manager','admin')
def add_location(shop_id):
    Shop.query.get_or_404(shop_id)
    data = request.get_json() or {}
    address = data.get('address')
    if not address:
        return jsonify({"Error": "Address required"}), 400
    l = Location(
        shop_id=shop_id,
        address=address,
        city=data.get('city'),
        state=data.get('state'),
        zipcode=data.get('zipcode')
    )
    db.session.add(l)
    db.session.commit()
    return jsonify({"Success": "Location successfully added", "location_id": l.location_id}), 201

# ----------------------
# Menu items
# ----------------------
@app.route('/shops/<int:shop_id>/menu', methods=['POST'])
@role_required('manager','admin')
def add_menu_item(shop_id):
    Shop.query.get_or_404(shop_id)
    data = request.get_json() or {}
    name = data.get('item_name')
    price = data.get('price')
    if not name or not price:
        return jsonify({"msg": "item_name and price required"}), 400
    it = MenuItem(
        shop_id=shop_id,
        item_name=name,
        description=data.get('description'),
        price=price,
        category=data.get('category')
    )
    db.session.add(it)
    db.session.commit()
    return jsonify({"Success": "Menu Item successfully added", "item_id": it.item_id}), 201

# ----------------------
# Reviews
# ----------------------
@app.route('/shops/<int:shop_id>/reviews', methods=['POST'])
@jwt_required()
def add_review(shop_id):
    s = Shop.query.get_or_404(shop_id)
    data = request.get_json() or {}
    rating = data.get('rating')
    text = data.get('review_text')
    if rating is None:
        return jsonify({"Error": "rating required"}), 400
    try:
        rating = int(rating)
    except:
        return jsonify({"Error": "rating must be an integer 1-5"}), 400
    if rating < 1 or rating > 5:
        return jsonify({"Error": "rating must be between 1 and 5"}), 400
    user_id = int(get_jwt_identity())
    r = Review(shop_id=shop_id, user_id=user_id, rating=rating, review_text=text) 
    db.session.add(r)
    db.session.commit()
    return jsonify({"Success": "Review successfully added", "review_id": r.review_id}), 201

# ----------------------
# Delete a user
# ----------------------
@app.route('/users/<int:user_id>', methods=['DELETE'])
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    current_user_id = int(get_jwt_identity())
    if user.user_id == current_user_id:
        return jsonify({"Error": "Cannot delete yourself"}), 400

    db.session.delete(user)
    db.session.commit()

    return jsonify({"Success": f"User {user.username} , id:{user.user_id} deleted successfully"})

# Initialize database
@app.cli.command("initdb")
def initdb():
    db.create_all()
    print("Tables created")

# Prepopulate database with coffeeshops
@app.cli.command("prepopulatedb")
def prepopulatedb():
    # Check if database is already populated
    if Shop.query.count() > 0 or User.query.count() > 0:
        print("Database already populated")
        return
    
    admin = User(
        username="admin",
        email="admin@email.com",
        password=bcrypt.generate_password_hash("admin").decode('utf-8'),
        role="admin"
    )
    
    manager = User(
        username="manager",
        email="manager@email.com",
        password=bcrypt.generate_password_hash("manager").decode('utf-8'),
        role="manager"
    )

    user = User(
        username="user",
        email="user@email.com",
        password=bcrypt.generate_password_hash("user").decode('utf-8'),
        role="user"
    )

    qahwah_house = Shop(
        shop_name="Qahwah House",
        description="Relaxed cafe specializing in honey-sweetened Yemeni coffee, as well as pastries like the honeycomb bread and Sabaya.",
        phone_num="516-214-6143",
        website="https://qahwahhouse.com/"
    )

    ny_caffeine = Shop(
        shop_name="NY Caffeine",
        description="Trendy coffee shop with a cozy atmosphere dishing up iced brews and hot cups, plus sweets.",
        phone_num="516-216-1683",
        website="https://www.nycaffeine.com/"
    )

    don_paco = Shop(
        shop_name="Don Paco Panadería & Café",
        description="Casual space serving popular Mexican desserts, tacos, breads, breakfasts and tortas along with coffee.",
        phone_num="516-280-2325",
        website="https://donpacolopez.com/"
    )

    print("Database prepopulated")

    db.session.add_all([admin, manager, user, qahwah_house, ny_caffeine, don_paco])
    db.session.commit()
 

if __name__ == '__main__':
    app.run(debug=True)



