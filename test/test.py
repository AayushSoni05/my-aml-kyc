from sqlalchemy import inspect
from app.database import engine

print("Database:", engine.url.database)
print("Tables:", inspect(engine).get_table_names())
print(
    "Customer columns:",
    [col["name"] for col in inspect(engine).get_columns("customer")]
)