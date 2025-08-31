# KoalaDB – A Beginner-Friendly Lightweight Database

KoalaDB is a **simple, file-based database** designed for beginners who want to understand how databases work without needing advanced tools like SQL or MongoDB.

It stores data in **collections** (similar to tables). Each collection contains **documents** (like JSON objects), and any media files (images, videos, PDFs, etc.) are saved inside a special `store/` folder.

---

## 📂 Database Structure

```
KoalaDB/
│── store/              # Stores media files
│── users/
│   └── data.bson       # User documents
│── products/
│   └── data.bson       # Product documents
```

---

## 🚀 Getting Started – Step by Step
### Install requirements
```bash
pip install -r requirements_koala.txt
```

### Step 1. Initialize the Database

```python
from koaladb import KoalaDB

# Create database folder and store/
KoalaDB.initialize("KoalaDB")
```

👉 Output:

```
Database initialized at /.../KoalaDB
Media store at /.../KoalaDB/store
```

---

### Step 2. Create a Collection

```python
KoalaDB.createCollection("users")
KoalaDB.createCollection("products")
```

👉 Creates folders:

```
KoalaDB/users/data.bson
KoalaDB/products/data.bson
```

---

### Step 3. Add Your First Document

```python
users = KoalaDB.collection("users")

# Create a new document
doc = users.create()
doc.add({"name": "Alice", "age": 25, "email": "alice@example.com"})
```

👉 Behind the scenes:

* A **unique ID** is assigned
* `_created_at` and `_updated_at` timestamps are added

---

### Step 4. Find Documents

```python
print(users.find())  # show all
print(users.find_one({"name": "Alice"}))
```

Example output:

```python
{
  "c8f1-...": {"name": "Alice", "age": 25, "email": "alice@example.com",
               "_created_at": 1725080912.3, "_updated_at": 1725080912.3}
}
```

---

### Step 5. Update Documents

```python
# Suppose Alice’s ID is "c8f1-..."
users.update("c8f1-...", {"age": 26})
```

👉 `_updated_at` auto-refreshes.

---

### Step 6. Delete Documents

```python
users.delete("c8f1-...")
```

👉 Also deletes any media linked to this document.

---

### Step 7. Store Media Files

```python
doc = users.create()
doc.add({"name": "Bob"})
doc.add_media_file("profile.png", "avatar")
```

👉 File is copied to `KoalaDB/store/` and linked in the document:

```python
"avatar": "store/uuid.png"
```

---

### Step 8. Work with Dates

```python
from datetime import datetime, timedelta

now = datetime.now()
yesterday = now - timedelta(days=1)

recent_docs = users.find_recent(hours=48)
old_docs = users.find_older_than(days=30)
```

👉 Super useful for logs, notes, or time-based data.

---

### Step 9. Browse in Web Viewer

Run:

```bash
python koaladb_consol.py --view
```

* Opens `http://localhost:8000`
* Shows all collections with a **clean web UI**
* Lets you:

  * ✅ View all documents
  * ✅ Search & sort
  * ✅ Edit fields directly
  * ✅ Add new fields

👉 To open a single collection:

```bash
python koaladb_consol.py --view --collection users
```

---

## 📘 Quick Reference of Common Functions

| **Action**        | **Code**                                 | **Benefit**        |
| ----------------- | ---------------------------------------- | ------------------ |
| Initialize DB     | `KoalaDB.initialize()`                   | Creates folders    |
| Create collection | `KoalaDB.createCollection("users")`      | Adds a new dataset |
| Insert doc        | `doc = users.create(); doc.add({...})`   | Adds data          |
| Find doc          | `users.find(query={...})`                | Query data         |
| Update doc        | `users.update(id, {"age": 30})`          | Modify fields      |
| Delete doc        | `users.delete(id)`                       | Remove data        |
| Count docs        | `users.count()`                          | Get totals         |
| Media support     | `doc.add_media_file("pic.png","avatar")` | Store files        |
| Web UI            | `python koaladb_consol.py --view`        | Browse & edit      |

---

## ✅ Why Use KoalaDB?

* 🐨 **Beginner-Friendly** → No SQL or setup needed.
* 📂 **Organized** → Collections, documents, and media are neatly stored.
* 🌐 **Web UI** → See and edit data visually in your browser.
* 🖼 **Media Ready** → Store and link files easily.
* 🕒 **Timestamps Built-in** → Track creation and updates.
* 🧪 **Great for Learning** → A sandbox before jumping into professional DBs.
