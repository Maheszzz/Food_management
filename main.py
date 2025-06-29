from fastapi import FastAPI
import mysql.connector
from typing import List
from pydantic import BaseModel
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

app = FastAPI()

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",  # Replace with your MySQL password
        database="foodtruck_monitoring"
    )

# Models for request/response
class Dessert(BaseModel):
    id: int
    name: str
    order_number: int
    timing: str

class Drink(BaseModel):
    id: int
    name: str
    quantity: int
    price: float

class Starter(BaseModel):
    id: int
    item_name: str
    spice_level: str
    price: float

class Order(BaseModel):
    order_id: int
    customer_name: str
    order_date: str
    total_amount: float
    dessert_id: int
    order_type: str

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "🍔 Food Truck Management API is running!"}

# Desserts
@app.get("/desserts", response_model=List[Dessert])
def get_desserts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM dessert_cart")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# Drinks
@app.get("/drinks", response_model=List[Drink])
def get_drinks():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM drinks_cart")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# Place a new order

security = HTTPBasic()

# Dummy user data for authentication
USER_DATA = {
    "staff": "password123"
}

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "staff")
    correct_password = secrets.compare_digest(credentials.password, USER_DATA["staff"])
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username

@app.post("/orders", response_model=Order)
def place_order(order: Order, username: str = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO customer_orders (order_id, customer_name, order_date, total_amount, dessert_id, order_type) VALUES (%s, %s, %s, %s, %s, %s)",
            (order.order_id, order.customer_name, order.order_date, order.total_amount, order.dessert_id, order.order_type)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()
    return order

# Revenue report
@app.get("/revenue")
def get_revenue(username: str = Depends(authenticate)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_amount) as total_revenue FROM customer_orders")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return {"total_revenue": result[0] if result and result[0] is not None else 0}

# Combined menu view
@app.get("/menu")
def get_menu():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    menu = {}
    cursor.execute("SELECT * FROM dessert_cart")
    menu["desserts"] = cursor.fetchall()
    cursor.execute("SELECT * FROM drinks_cart")
    menu["drinks"] = cursor.fetchall()
    cursor.execute("SELECT * FROM starters")
    menu["starters"] = cursor.fetchall()
    cursor.close()
    conn.close()
    return menu
@app.get("/starters", response_model=List[Starter])
def get_starters():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM starters")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# Orders
@app.get("/orders", response_model=List[Order])
def get_orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customer_orders")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
