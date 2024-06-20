from pydantic import BaseModel
from datetime import datetime
from typing import Optional  # Import Optional from typing


class UserOut(BaseModel):
    username: str
    email: str


class UserCreate(UserOut):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class ProductBase(BaseModel):
    name: str
    cost: float
    price: float
    stock_quantity: int


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    cost: Optional[float] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None


class ProductUpdateOut(BaseModel):
    id: int
    name: Optional[str] = None
    cost: Optional[float] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None

    class Config:
        orm_mode = True


class SaleBase(BaseModel):
    quantity: int
    pid: int


class SaleCreate(SaleBase):
    pass


class SaleOut(BaseModel):
    quantity: int
    pid: int
    total_price: float
    sold_at: datetime
    product_id: int

    class Config:
        orm_mode = True
        from_orm = True


class SaleUpdate(BaseModel):
    quantity: Optional[int] = None
    pid: Optional[int] = None


class SaleUpdateOut(BaseModel):
    id: int
    quantity: Optional[int] = None
    pid: Optional[int] = None
    total_price: Optional[float] = None

    class Config:
        orm_mode = True


class Sale(SaleBase):
    id: int
    quantity: int
    pid: int
    total_price: float
    sold_at: datetime
    product_id: int

    class Config:
        orm_mode = True


class PaymentResponse(BaseModel):
    receipt_filename: str


class PaymentCreate(PaymentResponse):
    payment_method: str 


class CustomerBase(BaseModel):
    name: str
    email: str


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    id: int
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class ExpenseBase(BaseModel):
    amount: float
    description: Optional[str]


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseOut(ExpenseBase):
    id: int
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
