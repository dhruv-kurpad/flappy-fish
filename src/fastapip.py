from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pyodbc
import os
app = FastAPI()


def row_to_dict(cursor, row):
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def get_db():
    conn = pyodbc.connect(
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server={os.getenv('SERVER')};"
            f"Database={os.getenv('DATABASE')};"
            f"Uid={os.getenv('UID')};"
            f"Pwd={os.getenv('PWD')};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
        )
    return conn

class RegLoginModel(BaseModel):
    username: str
    password: str

class DeleteModel(BaseModel):
    username: str

class UpdateScoreModel(BaseModel):
    username: str
    score: int

@app.get("/")
def root():
    return {"message": "Hello from FastAPI"}

@app.get("/players")
def get_test():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dbo.players")
    rows = cursor.fetchall()
    players = [row_to_dict(cursor, row) for row in rows]
    conn.close()
    return players

@app.post("/register", status_code=201)
def register(data: RegLoginModel):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO dbo.players (username, password) VALUES (?, ?)",
        (data.username, data.password),
    )
    conn.commit()
    conn.close()
    return {"message": "Player added successfully"}

@app.get("/login")
def login(data: RegLoginModel):
    conn = get_db()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT * FROM dbo.players WHERE username = ? AND password = ?",
        (data.username, data.password)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid username or password")
    result = row_to_dict(cursor, row)
    conn.close()
    return result

@app.delete("/delete")
def delete(data: DeleteModel):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dbo.players WHERE username = ?", (data.username,))
    conn.commit()
    conn.close()
    return {"message": f"Deleted user {data.username}"}

@app.put("/updateScore")
def update_score(data: UpdateScoreModel):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE dbo.players SET high_score = ? WHERE username = ?",
        (data.score, data.username)
    )
    conn.commit()
    conn.close()
    return {"message": f"Updated score for {data.username} to {data.score}"}