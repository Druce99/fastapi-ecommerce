from pydantic import BaseModel

class OrderCreated(BaseModel):
    order_id: int
    email: str

class UserRegistered(BaseModel):
    email: str