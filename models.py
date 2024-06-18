from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Kevin254!@localhost/myduka_api"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    products = relationship("Product", back_populates="user")
    sales = relationship("Sale", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    cost = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(
        DateTime, default=datetime.datetime.utcnow, nullable=False)
    stock_quantity = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="products")
    sales = relationship("Sale", back_populates="product")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float)
    sold_at = Column(
        DateTime, default=datetime.datetime.utcnow, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    is_paid = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    product = relationship("Product", back_populates="sales")
    payments = relationship("Payment", back_populates="sale")
    user = relationship("User", back_populates="sales")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    payment_method = Column(String)
    amount = Column(Float)
    payment_date = Column(
        DateTime, default=datetime.datetime.utcnow, nullable=False)

    sale = relationship("Sale", back_populates="payments")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="payments")


# Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
