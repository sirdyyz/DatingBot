from fastapi import FastAPI
from pydantic import BaseModel
from database import SessionLocal, engine
from models import Base, Customer, Product, Order, OrderItem

app = FastAPI()

Base.metadata.create_all(bind=engine)

class ItemSchema(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderSchema(BaseModel):
    customer_id: int
    items: list[ItemSchema]

@app.post("/create_order")
def create_order(data: OrderSchema):
    db = SessionLocal()
    try:
        new_order = Order(CustomerID=data.customer_id)
        db.add(new_order)
        db.flush()

        total_amount = 0

        for item in data.items:
            sub = item.quantity * item.price
            total_amount += sub
            
            oi = OrderItem(
                OrderID=new_order.OrderID, 
                ProductID=item.product_id, 
                Quantity=item.quantity, 
                Subtotal=sub
            )
            db.add(oi)
        
        new_order.TotalAmount = total_amount
        db.commit()
        return {"status": "все ок", "message": "заказ оформлен"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


class EmailSchema(BaseModel):
    customer_id: int
    new_email: str

@app.put("/update_email")
def update_email(data: EmailSchema):
    db = SessionLocal()
    try:
        c = db.query(Customer).filter(Customer.CustomerID == data.customer_id).with_for_update().first()
        if c:
            c.Email = data.new_email
            db.commit()
            return {"status": "все ок", "message": "почта обновлена"}
        else:
            return {"status": "error", "message": "не нашли клиента"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


class ProductSchema(BaseModel):
    name: str
    price: float

@app.post("/add_product")
def add_new_product(data: ProductSchema):
    db = SessionLocal()
    try:
        p = Product(ProductName=data.name, Price=data.price)
        db.add(p)
        db.commit()
        return {"status": "все ок", "message": "товар добавлен"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()