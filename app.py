from flask import Flask, jsonify, render_template, request
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "retail_sales.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/v1/kpis", methods=["GET"])
def get_kpis():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT Sales, Profit, Order_ID, Returned, Customer_Rating FROM sales", conn)
        conn.close()

        if df.empty:
            return jsonify({"error": "No data found in database"}), 404

        total_sales = float(df['Sales'].sum())
        total_profit = float(df['Profit'].sum())
        total_orders = int(df['Order_ID'].nunique())
        avg_rating = float(df['Customer_Rating'].mean())
        return_rate = float((df['Returned'] == 'Yes').mean() * 100)

        return jsonify({
            "total_sales": round(total_sales, 2),
            "total_profit": round(total_profit, 2),
            "total_orders": total_orders,
            "avg_rating": round(avg_rating, 2),
            "return_rate": round(return_rate, 2)
        })
    except Exception as e:
        print(f"Error in /api/v1/kpis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/sales-trend", methods=["GET"])
def get_sales_trend():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT Order_Date, Sales, Profit FROM sales", conn)
        conn.close()

        df['Order_Date'] = pd.to_datetime(df['Order_Date'])
        df['Month'] = df['Order_Date'].dt.to_period('M').astype(str)

        monthly = df.groupby('Month').agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
        monthly = monthly.sort_values('Month')

        return jsonify({
            "labels": monthly['Month'].tolist(),
            "sales": monthly['Sales'].round(2).tolist(),
            "profit": monthly['Profit'].round(2).tolist()
        })
    except Exception as e:
        print(f"Error in /api/v1/sales-trend: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/category-performance", methods=["GET"])
def get_category_performance():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT Category, Sales, Profit FROM sales", conn)
        conn.close()

        cat_df = df.groupby('Category').agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()

        return jsonify({
            "categories": cat_df['Category'].tolist(),
            "sales": cat_df['Sales'].round(2).tolist(),
            "profit": cat_df['Profit'].round(2).tolist()
        })
    except Exception as e:
        print(f"Error in /api/v1/category-performance: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/customer-segments", methods=["GET"])
def get_customer_segments():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT Customer_Segment, COUNT(DISTINCT Customer_ID) as count FROM sales GROUP BY Customer_Segment", conn)
        conn.close()

        return jsonify({
            "segments": df['Customer_Segment'].tolist(),
            "counts": df['count'].tolist()
        })
    except Exception as e:
        print(f"Error in /api/v1/customer-segments: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json() or {}
        quantity = float(data.get("quantity", 1))
        unit_price = float(data.get("unit_price", 0))
        discount = float(data.get("discount", 0))

        gross = quantity * unit_price
        predicted_sales = gross * (1 - (discount / 100.0))
        estimated_profit = predicted_sales * 0.15 

        return jsonify({
            "predicted_sales": round(predicted_sales, 2),
            "estimated_profit": round(estimated_profit, 2)
        })
    except Exception as e:
        print(f"Error in /api/v1/predict: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)