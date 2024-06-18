from fastapi import FastAPI,HTTPException,Depends
import uvicorn
from datetime import timedelta,datetime,timezone
from models import SessionLocal,User,Product,Sale,Payment
from pydatic_models import UserCreate, UserLogin, ProductCreate,\
UserOut, ProductBase, ProductUpdate, ProductUpdateOut,SaleCreate,SaleUpdate,SaleUpdateOut,SaleOut,PaymentResponse,PaymentCreate
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from auth import pwd_context,authenticate_user,create_access_token,ACCESS_TOKEN_EXPIRE_MINUTES,get_current_user
import pytz
import sentry_sdk
from fastapi.security.oauth2 import OAuth2AuthorizationCodeBearer
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config
from starlette.requests import Request
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from typing import List
from fastapi.responses import FileResponse

# sentry configuration

# sentry_sdk.init(
#     dsn="https://345b82786553390dd6a47ffff274755c@o4507327886196736.ingest.us.sentry.io/4507327888556032",
#     traces_sample_rate=1.0,
#     profiles_sample_rate=1.0,
# )
app=FastAPI()

origins=[
    "http://localhost:5173", "http://localhost:3000"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST","PUT"],
    allow_headers=["Authorization", "Content-Type"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Define OAuth2 scheme
# oauth2_scheme = OAuth2AuthorizationCodeBearer(
#     authorizationUrl='https://accounts.google.com/o/oauth2/auth',
#     tokenUrl='https://accounts.google.com/o/oauth2/token'
# )
# get users


@app.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
# register user

@app.post("/register" ,response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=400, detail="Username already registered")
    password = pwd_context.hash(user.password)
    db_user = User(username=user.username,email=user.email, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return db_user


# # login user
# @app.get("/google-login")
# async def login(request: Request):
#     redirect_uri = request.url_for('auth')
#     return await oauth.google.authorize_redirect(request, redirect_uri)


# @app.get("/auth")
# async def auth(request: Request, db: Session = Depends(get_db)):
#     token = await oauth.google.authorize_access_token(request)
#     user_info = await oauth.google.parse_id_token(token)

    # Register or get user
    # user = db.query(User).filter(User.email == user_info["email"]).first()
    # if not user:
    #     user = User(username=user_info["email"],
    #                 email=user_info["email"], password="")
    #     db.add(user)
    #     db.commit()
    #     db.refresh(user)

    # # You might want to return some response here
    # # For example, you can return the user's information
    # return {"user": user_info}



@app.post("/login")
def login(user: UserLogin):
    db_user = authenticate_user(user.username, user.password)
    if not db_user:
        raise HTTPException(
            status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    print(access_token)
    return {"access_token": access_token, "token_type": "bearer"}


 

# get products
@app.get("/products")
def get_products(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    products = db.query(Product).filter(
        Product.user_id == current_user.id).all()
    db.close()
    print(products)
    return products


# post products
@app.post("/products")
def create_product(product: ProductCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_product = Product(**product.model_dump(), user_id=current_user.id)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    db.close()
    return db_product

# put products 
@app.put("/products/{pid}")
async def update_product(pid: int, product: ProductUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), response_model = Product):
    prod = db.query(Product).filter(Product.id == pid,
                                    Product.user_id == current_user.id).first()
    if not prod :
        raise HTTPException(status_code=404,detail="product does not exist")

    if not prod.name == product.name and product.name is not None:
        prod.name = product.name

    if not prod.cost == product.cost and product.cost is not None:
        prod.cost = product.cost
    
    if not prod.price == product.price and product.price is not None:
        prod.price = product.price
    
    if not prod.stock_quantity == product.stock_quantity and product.stock_quantity is not None:
        prod.stock_quantity = product.stock_quantity

    db.commit()

    prod = db.query(Product).filter(Product.id == pid).first()
    return prod

# get sales

@app.get("/sales")
def get_sales(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sales = db.query(Sale).join(Product).filter(
        Product.user_id == current_user.id).all()
    print(sales)
    db.close()
    return sales
 
# post sales 


@app.post("/sales")
def make_sale(sale: SaleCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == sale.pid,
                                       Product.user_id == current_user.id).first()
    print (product)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock_quantity < sale.quantity:
        raise HTTPException(
            status_code=400, detail="Insufficient stock quantity")
    
    print(product.stock_quantity)

    total_price = product.price * sale.quantity

    product.stock_quantity -= sale.quantity
    print(product.stock_quantity)

    db_sale = Sale(quantity=sale.quantity,
                   total_price=total_price, product_id=sale.pid, user_id=current_user.id)
    db.add(db_sale)

    db.commit()
    db.refresh(db_sale)

    return db_sale

# update sale 


@app.put("/sales/{sale_id}", response_model=SaleUpdateOut)
async def update_sale(sale_id: int, sale_update: SaleUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sale = db.query(Sale).join(Product).filter(Sale.id == sale_id,
                                               Product.user_id == current_user.id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    sale.quantity = sale_update.quantity
    sale.pid = sale_update.pid
    db.commit()

    return sale

# sales per day

@app.get("/sales_per_day")
def sales_per_day(current_user: User = Depends(get_current_user)):
    today = datetime.now(pytz.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    sales = (
        SessionLocal().query(func.date(Sale.sold_at), func.sum(Sale.quantity*Product.price))
        .filter(Sale.product.has(user_id=current_user.id), Sale.sold_at >= today)
        .group_by(func.date(Sale.sold_at))
        .all()
    )
    dates = [sale[0].isoformat() for sale in sales]
    counts = [sale[1] for sale in sales]
    return {"data": [{"x": dates, "y": counts, "type": "line", "name": "Sales per Day"}]}


# profit per day
@app.get("/profit_per_day")
def profit_per_day(current_user: User = Depends(get_current_user)):
    today = datetime.now(pytz.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    sales = (
        SessionLocal().query(func.date(Sale.sold_at), func.sum(Sale.total_price))
        .filter(Sale.product.has(user_id=current_user.id), Sale.sold_at >= today)
        .group_by(func.date(Sale.sold_at))
        .all()
    )
    dates = [sale[0] for sale in sales]
    profits = [sale[1] for sale in sales]
    return {"data": [{"x": dates, "y": profits, "type": "line", "name": "Profit per Day"}]}

# sales per product

@app.get("/sales_per_product")
def sales_per_product(current_user: User = Depends(get_current_user)):
    products = (
        SessionLocal().query(Product.id, Product.name, func.count(Sale.id))
        .join(Sale)
        .filter(Product.user_id == current_user.id)
        .group_by(Product.id, Product.name)
        .all()
    )
    product_names = [product[1] for product in products]
    sales_counts = [product[2] for product in products]
    return {"data": [{"x": product_names, "y": sales_counts, "type": "bar", "name": "Sales per Product"}]}


# profit per product 
@app.get("/profit_per_product")
def profit_per_product(current_user: User = Depends(get_current_user)):
    products = (
        SessionLocal().query(Product.id, Product.name, func.sum(Sale.total_price))
        .join(Sale)
        .filter(Product.user_id == current_user.id)
        .group_by(Product.id, Product.name)
        .all()
    )
    product_names = [product[1] for product in products]
    profits = [product[2] for product in products]
    return {"data": [{"x": product_names, "y": profits, "type": "bar", "name": "Profit per Product"}]}

    # payment


def get_unpaid_sales(db: Session = Depends(SessionLocal), current_user: User = Depends(get_current_user)):
    try:
        # user = db.query(User).filter(User.username ==
        #                              current_user.username).first()
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")

        unpaid_sales = db.query(Sale).filter(
            Sale.is_paid == False ).all()

        unpaid_sales_list = []
        for sale in unpaid_sales:
            unpaid_sales_list.append({
                "id": sale.id,
                "product_name": sale.product.name,
                "quantity": sale.quantity,
                "total_price": sale.total_price
            })

        # user_id = user.id
        # print(f"User ID: {user_id}")

        return unpaid_sales_list

    finally:
        db.close()

def mark_sales_as_paid(db: Session, sale_ids: List[int]):
    db.query(Sale).filter(Sale.id.in_(sale_ids)).update(
        {"is_paid": True}, synchronize_session=False)
    db.commit()


def process_payment(db: Session, sale_ids: List[int], payment_method: str, total_amount: float, current_user: User):
    unpaid_sales = db.query(Sale).filter(Sale.id.in_(sale_ids)).all()
    if not unpaid_sales:
        raise HTTPException(status_code=404, detail="No unpaid sales found.")

    for sale in unpaid_sales:
        sale.is_paid = True
        db_payment = Payment(
            sale_id=sale.id, payment_method=payment_method, amount=sale.total_price)
        db.add(db_payment)

    db.commit()

    receipt_filename = generate_receipt(
        sale_ids, total_amount, payment_method, db, current_user)
    return {"receipt_filename": receipt_filename, "total_amount": total_amount}

# Receipt generation


def generate_receipt(sale_ids: List[int], total_amount: float, payment_method: str, db: Session, current_user: User):
    sales = db.query(Sale).filter(Sale.id.in_(sale_ids)).all()
    receipt_filename = f"receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    pdf = canvas.Canvas(receipt_filename, pagesize=letter)
    pdf.setTitle("Receipt")

    # Header
    pdf.drawString(100, 750, "Receipt")
    pdf.drawString(100, 735, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.drawString(100, 720, f"Payment Method: {payment_method}")

    # Table Headers
    pdf.drawString(100, 700, "Product Name")
    pdf.drawString(250, 700, "Username")
    pdf.drawString(400, 700, "Quantity")
    pdf.drawString(500, 700, "Total Price")

    y_position = 680

    # Sales Details
    for sale in sales:
        product = db.query(Product).filter(
            Product.id == sale.product_id).first()
        pdf.drawString(100, y_position, str(product.name))  # Product Name
        pdf.drawString(400, y_position, str(sale.quantity))  # Quantity
        pdf.drawString(500, y_position, f"${\
                       sale.total_price:.2f}")  # Total Price
        y_position -= 20

    # Total Amount and Server Information
    pdf.drawString(100, y_position - 20, f"Total Amount: ${total_amount:.2f}")
    pdf.drawString(100, y_position - 40, f"Served by: {current_user.username}")

    # Save PDF
    pdf.save()
    return receipt_filename


@app.get("/unpaid_sales")
def fetch_unpaid_sales(db: Session = Depends(get_db)):
    sales = get_unpaid_sales(db)
    return sales


@app.post("/payments", response_model=PaymentResponse)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    unpaid_sales = db.query(Sale).filter(Sale.is_paid == False).all()
    if not unpaid_sales:
        raise HTTPException(status_code=404, detail="No unpaid sales found.")

    sale_ids = [sale.id for sale in unpaid_sales]
    total_amount = sum(sale.total_price for sale in unpaid_sales)
    mark_sales_as_paid(db, sale_ids)
    payment_info = process_payment(
        db, sale_ids, payment.payment_method, total_amount, current_user)
    return payment_info


@app.get("/receipts/{receipt_filename}")
def get_receipt(receipt_filename: str):
    return FileResponse(receipt_filename, media_type='application/pdf', filename=receipt_filename)


if __name__ == "__main__":
    config = uvicorn.Config("main:app", port=8000,
                            log_level="info", reload=True)
    server = uvicorn.Server(config)
    server.run()
