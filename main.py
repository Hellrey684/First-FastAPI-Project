from fastapi import FastAPI
from pydantic import BaseModel
from database import create_tables, get_db

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

app = FastAPI()
create_tables()

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/items/")
def get_items():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    conn.close()
    return {"items": rows}

@app.post("/items/")
def create_item(item: Item):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO items (name, price, is_offer) VALUES (?, ?, ?)",
        (item.name, item.price, item.is_offer)
    )
    conn.commit()
    conn.close()
    return {"message": "Item created", "id": cursor.lastrowid}
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {"message": f"Item {item_id} deleted"}
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET name=?, price=?, is_offer=? WHERE id=?", (item.name, item.price, item.is_offer, item_id))
    conn.commit()
    conn.close()
    return {"message": f"Item {item_id} update"}