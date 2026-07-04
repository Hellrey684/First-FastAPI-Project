from fastapi import FastAPI
from pydantic import BaseModel
from database import create_tables, get_db
from fastapi.middleware.cors import CORSMiddleware
class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = False

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # разрешаем запросы с любых доменов
    allow_credentials=True,
    allow_methods=["*"],  # разрешаем все методы (GET, POST, OPTIONS и др.)
    allow_headers=["*"],  # разрешаем все заголовки
)
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
def get_db():
    conn = sqlite3.connect("items.db")
    conn.row_factory = sqlite3.Row
    return conn

# Инициализация таблицы и тестовых данных
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        sample = [
            ("Товар A", 5.0),
            ("Товар B", 10.0),
            ("Товар C", 15.0),
            ("Товар D", 20.0),
        ]
        cursor.executemany("INSERT INTO items (name, price) VALUES (?, ?)", sample)
        conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

# ---------- ЭНДПОИНТ 1: все товары ----------
@app.get("/items/")
def get_all_items():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    conn.close()
    return {"items": [dict(row) for row in rows]}

# ---------- ЭНДПОИНТ 2: один товар по ID ----------
@app.get("/items/{item_id}")
def get_item(item_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return dict(row)

# ---------- ЭНДПОИНТ 3: фильтр по цене ----------
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