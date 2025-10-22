from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

router = APIRouter(
    prefix="/pizza",
    tags=["Pizza"]
)

# Pydantic Models
class CartItem(BaseModel):
    pizzaId: int
    name: str
    quantity: int
    unitPrice: float
    totalPrice: float

class OrderCreate(BaseModel):
    customer: str
    phone: str
    address: str
    priority: bool = False
    cart: List[CartItem]
    position: Optional[str] = ""

class OrderUpdate(BaseModel):
    priority: bool

class Order(BaseModel):
    id: str
    customer: str
    phone: str
    address: str
    status: str
    priority: bool
    priorityPrice: float
    orderPrice: float
    estimatedDelivery: str
    cart: List[CartItem]
    position: str

class MenuItem(BaseModel):
    id: int
    name: str
    unitPrice: float
    imageUrl: str
    ingredients: List[str]
    soldOut: bool

# In-memory storage (replace with database in production)
menu_items = [
  {
    "id": 1,
    "name": "Margherita",
    "unitPrice": 12,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-1.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "basil"
    ],
    "soldOut": False
  },
  {
    "id": 2,
    "name": "Capricciosa",
    "unitPrice": 14,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-2.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "ham",
      "mushrooms",
      "artichoke"
    ],
    "soldOut": True
  },
  {
    "id": 3,
    "name": "Romana",
    "unitPrice": 15,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-3.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "prosciutto"
    ],
    "soldOut": False
  },
  {
    "id": 4,
    "name": "Prosciutto e Rucola",
    "unitPrice": 16,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-4.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "prosciutto",
      "arugula"
    ],
    "soldOut": False
  },
  {
    "id": 5,
    "name": "Diavola",
    "unitPrice": 16,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-5.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "spicy salami",
      "chili flakes"
    ],
    "soldOut": False
  },
  {
    "id": 6,
    "name": "Vegetale",
    "unitPrice": 13,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-6.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "bell peppers",
      "onions",
      "mushrooms"
    ],
    "soldOut": False
  },
  {
    "id": 7,
    "name": "Napoli",
    "unitPrice": 16,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-7.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "fresh tomato",
      "basil"
    ],
    "soldOut": False
  },
  {
    "id": 8,
    "name": "Siciliana",
    "unitPrice": 16,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-8.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "anchovies",
      "olives",
      "capers"
    ],
    "soldOut": True
  },
  {
    "id": 9,
    "name": "Pepperoni",
    "unitPrice": 14,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-9.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "pepperoni"
    ],
    "soldOut": False
  },
  {
    "id": 10,
    "name": "Hawaiian",
    "unitPrice": 15,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-10.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "pineapple",
      "ham"
    ],
    "soldOut": False
  },
  {
    "id": 11,
    "name": "Spinach and Mushroom",
    "unitPrice": 15,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-11.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "spinach",
      "mushrooms"
    ],
    "soldOut": False
  },
  {
    "id": 12,
    "name": "Mediterranean",
    "unitPrice": 16,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-12.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "sun-dried tomatoes",
      "olives",
      "artichoke"
    ],
    "soldOut": False
  },
  {
    "id": 13,
    "name": "Greek",
    "unitPrice": 16,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-13.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "spinach",
      "feta",
      "olives",
      "pepperoncini"
    ],
    "soldOut": True
  },
  {
    "id": 14,
    "name": "Abruzzese",
    "unitPrice": 16,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-14.jpg",
    "ingredients": [
      "tomato",
      "mozzarella",
      "prosciutto",
      "arugula"
    ],
    "soldOut": False
  },
  {
    "id": 15,
    "name": "Pesto Chicken",
    "unitPrice": 16,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-15.jpg",
    "ingredients": [
      "pesto",
      "mozzarella",
      "chicken",
      "sun-dried tomatoes",
      "spinach"
    ],
    "soldOut": False
  },
  {
    "id": 16,
    "name": "Eggplant Parmesan",
    "unitPrice": 15,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-16.jpg",
    "ingredients": [
      "marinara",
      "mozzarella",
      "eggplant",
      "parmesan"
    ],
    "soldOut": False
  },
  {
    "id": 17,
    "name": "Roasted Veggie",
    "unitPrice": 15,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-17.jpg",
    "ingredients": [
      "marinara",
      "mozzarella",
      "zucchini",
      "eggplant",
      "peppers",
      "onions"
    ],
    "soldOut": False
  },
  {
    "id": 18,
    "name": "Tofu and Mushroom",
    "unitPrice": 15,
    "imageUrl": "https://dclaevazetcjjkrzczpc.supabase.co/storage/v1/object/public/pizzas/pizza-18.jpg",
    "ingredients": [
      "marinara",
      "mozzarella",
      "tofu",
      "mushrooms",
      "bell peppers"
    ],
    "soldOut": False
  }
]

orders_db = {}

# Routes
@router.get("/menu")
async def get_menu():
    """Get all menu items"""
    return {"data": menu_items}

@router.get("/order/{order_id}")
async def get_order(order_id: str):
    """Get a specific order by ID"""
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Couldn't find order #{order_id}"
        )
    return {"data": orders_db[order_id]}

@router.post("/order", status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate):
    """Create a new order"""
    try:
        # Generate unique order ID
        order_id = str(uuid.uuid4())[:8].upper()
        
        # Calculate prices
        order_price = sum(item.totalPrice for item in order.cart)
        priority_price = order_price * 0.2 if order.priority else 0.0
        
        # Calculate estimated delivery (30 minutes + 20 if priority)
        delivery_time = 30 if not order.priority else 20
        estimated_delivery = (
            datetime.utcnow() + timedelta(minutes=delivery_time)
        ).isoformat()
        
        # Create order object
        new_order = {
            "id": order_id,
            "customer": order.customer,
            "phone": order.phone,
            "address": order.address,
            "status": "preparing",
            "priority": order.priority,
            "priorityPrice": priority_price,
            "orderPrice": order_price,
            "estimatedDelivery": estimated_delivery,
            "cart": [item.dict() for item in order.cart],
            "position": order.position
        }
        
        # Store order
        orders_db[order_id] = new_order
        
        return {"data": new_order}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed creating your order"
        )

@router.patch("/order/{order_id}")
async def update_order(order_id: str, update_data: OrderUpdate):
    """Update an existing order (e.g., make it priority)"""
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Couldn't find order #{order_id}"
        )
    
    try:
        order = orders_db[order_id]
        
        # Update priority
        if update_data.priority and not order["priority"]:
            order["priority"] = True
            order["priorityPrice"] = order["orderPrice"] * 0.2
            
            # Update estimated delivery time
            current_delivery = datetime.fromisoformat(order["estimatedDelivery"])
            new_delivery = current_delivery - timedelta(minutes=10)
            order["estimatedDelivery"] = new_delivery.isoformat()
        
        orders_db[order_id] = order
        
        return {"data": order}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed updating your order"
        )