import pandas as pd
import sqlite3

def init_db(csv_filepath="sales.csv", db_filepath="retail_sales.db"):
    df = pd.read_csv(csv_filepath)

    # Convert date columns
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y', errors='coerce')
    df['Ship_Date'] = pd.to_datetime(df['Ship_Date'], format='%d-%m-%Y', errors='coerce')

    # Handle missing values
    df['Email'] = df['Email'].fillna('unknown@example.com')
    df['Phone'] = df['Phone'].fillna(0)
    df['Discount'] = df['Discount'].fillna(0.0)
    df['Customer_Rating'] = df['Customer_Rating'].fillna(df['Customer_Rating'].mean())

    # Format dates back to standard ISO string for SQLite
    df['Order_Date'] = df['Order_Date'].dt.strftime('%Y-%m-%d')
    df['Ship_Date'] = df['Ship_Date'].dt.strftime('%Y-%m-%d')

    conn = sqlite3.connect(db_filepath)
    df.to_sql('sales', conn, if_exists='replace', index=False)
    conn.close()
    print("Database initialized successfully with cleaned sales data.")

if __name__ == "__main__":
    init_db()