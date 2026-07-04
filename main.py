from fastapi import FastAPI
from pydantic import BaseModel
from database import create_tables, get_db
from fastapi.middleware.cors import CORSMiddleware

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

@app.get("/")
def root():
    return {"message": "Hello World"}

# ---------- СНАЧАЛА КОНКРЕТНЫЕ МАРШРУТЫ ----------
@app.get("/items/stats/")
def get_stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM items")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(price) FROM items")
    avg_price = cursor.fetchone()[0] or 0

    cursor.execute("SELECT MIN(price), MAX(price) FROM items")
    min_price, max_price = cursor.fetchone()
    if min_price is None:
        min_price = 0
        max_price = 0

    cursor.execute("SELECT COUNT(*) FROM items WHERE is_offer = 1")
    with_offer = cursor.fetchone()[0]

    conn.close()
    return {
        "total": total,
        "avg_price": round(avg_price, 2),
        "min_price": min_price,
        "max_price": max_price,
        "with_offer": with_offer
    }

@app.get("/items/filter/")
def filter_items(min_price: float = None, max_price: float = None):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM items WHERE 1=1"
    params = []

    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)

    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return {"items": [dict(row) for row in rows]}

# ---------- ПОТОМ ОБЩИЕ МАРШРУТЫ ----------
@app.get("/items/")
def get_items():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    conn.close()
    return {"items": rows}

@app.get("/items/{item_id}")
def get_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"error": "Item not found"}, 404
    return dict(row)

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

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE items SET name=?, price=?, is_offer=? WHERE id=?",
        (item.name, item.price, item.is_offer, item_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        return {"error": "Item not found"}, 404
    conn.commit()
    conn.close()
    return {"message": f"Item {item_id} updated"}

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    if cursor.rowcount == 0:
        conn.close()
        return {"error": "Item not found"}, 404
    conn.commit()
    conn.close()
    return {"message": f"Item {item_id} deleted"}