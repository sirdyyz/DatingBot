import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'Customers'
    CustomerID = Column(Integer, primary_key=True)
    FirstName = Column(String)
    LastName = Column(String)
    Email = Column(String)

class Product(Base):
    __tablename__ = 'Products'
    ProductID = Column(Integer, primary_key=True)
    ProductName = Column(String)
    Price = Column(Float)

class Order(Base):
    __tablename__ = 'Orders'
    OrderID = Column(Integer, primary_key=True)
    CustomerID = Column(Integer, ForeignKey('Customers.CustomerID'))
    OrderDate = Column(DateTime, default=datetime.datetime.now)
    TotalAmount = Column(Float, default=0.0)

class OrderItem(Base):
    __tablename__ = 'OrderItems'
    OrderItemID = Column(Integer, primary_key=True)
    OrderID = Column(Integer, ForeignKey('Orders.OrderID'))
    ProductID = Column(Integer, ForeignKey('Products.ProductID'))
    Quantity = Column(Integer)
    Subtotal = Column(Float)