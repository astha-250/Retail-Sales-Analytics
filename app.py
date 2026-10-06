from flask import Flask, jsonify, render_template, request
import sqlite3
import pandas as pd
import numpy as np
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
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/sales-trend", methods=["GET"])
def get_sales_trend():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT Order_Date, Sales, Profit FROM sales", conn)
        conn.close()

        if df.empty:
            return jsonify({"labels": [], "sales": [], "profit": []})

        # Parse dates flexibly regardless of initial formatting
        df['Order_Date'] = pd.to_datetime(df['Order_Date'], errors='coerce')
        df = df.dropna(subset=['Order_Date'])

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
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/top-products", methods=["GET"])
def get_top_products():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT Product_Name, Sales FROM sales", conn)
        conn.close()

        top_df = df.groupby('Product_Name')['Sales'].sum().nlargest(10).reset_index()

        return jsonify({
            "products": top_df['Product_Name'].tolist(),
            "sales": top_df['Sales'].round(2).tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/region-sales", methods=["GET"])
def get_region_sales():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT Region, Sales FROM sales", conn)
        conn.close()

        reg_df = df.groupby('Region')['Sales'].sum().reset_index()

        return jsonify({
            "regions": reg_df['Region'].tolist(),
            "sales": reg_df['Sales'].round(2).tolist()
        })
    except Exception as e:
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
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/correlation", methods=["GET"])
def get_correlation():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM sales", conn)
        conn.close()

        # Define numeric columns present in the dataset
        numeric_cols = ['Age', 'Phone', 'Quantity', 'Unit_Price', 'Discount', 'Sales', 'Cost', 'Profit', 'Delivery_Days', 'Customer_Rating']
        
        # Filter only existing numeric columns from the DataFrame
        existing_cols = [col for col in numeric_cols if col in df.columns]
        
        # Convert values to float and fill NaNs
        numeric_df = df[existing_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # Drop columns with zero variance (all values constant) to avoid NaN correlations
        numeric_df = numeric_df.loc[:, (numeric_df != numeric_df.iloc[0]).any()]

        # Compute correlation matrix
        corr = numeric_df.corr().fillna(0).round(4)

        return jsonify({
            "features": corr.columns.tolist(),
            "matrix": corr.values.tolist()
        })
    except Exception as e:
        print(f"Error computing correlation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/sales-outliers", methods=["GET"])
def get_sales_outliers():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT Sales FROM sales", conn)
        conn.close()

        # Ensure numeric type
        sales = pd.to_numeric(df['Sales'], errors='coerce').dropna().sort_values().values

        if len(sales) == 0:
            return jsonify({"error": "No sales data available"}), 400

        # Calculate Boxplot Statistics (IQR)
        q1 = float(np.percentile(sales, 25))
        median = float(np.median(sales))
        q3 = float(np.percentile(sales, 75))
        iqr = q3 - q1

        lower_bound = float(max(sales.min(), q1 - 1.5 * iqr))
        upper_bound = float(q3 + 1.5 * iqr)

        # Identify outliers beyond upper bound
        outliers = [float(x) for x in sales if x > upper_bound or x < lower_bound]

        return jsonify({
            "min": float(sales.min()),
            "q1": q1,
            "median": median,
            "q3": q3,
            "max": float(sales.max()),
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "outlier_count": len(outliers),
            "outliers_sample": outliers[-20:] # Send last 20 extreme outliers
        })
    except Exception as e:
        print(f"Sales Outliers API Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/product-performance", methods=["GET"])
def get_product_performance():
    try:
        conn = get_db_connection()
        # Group by Product_Name (or Product_ID) to sum Total Sales and Total Profit
        df = pd.read_sql_query("""
            SELECT Product_Name, SUM(Sales) as Total_Sales, SUM(Profit) as Total_Profit
            FROM sales
            GROUP BY Product_Name
        """, conn)
        conn.close()

        # Format points as [{x: Total_Sales, y: Total_Profit, name: Product_Name}, ...]
        data_points = [
            {
                "x": float(row['Total_Sales']),
                "y": float(row['Total_Profit']),
                "name": str(row['Product_Name'])
            }
            for _, row in df.iterrows()
        ]

        return jsonify({"products": data_points})
    except Exception as e:
        print(f"Product Performance API Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/top-return-products", methods=["GET"])
def get_top_return_products():
    try:
        conn = get_db_connection()
        
        # Check column name safely (Product_Name or Product)
        df_cols = pd.read_sql_query("SELECT * FROM sales LIMIT 1", conn)
        prod_col = 'Product_Name' if 'Product_Name' in df_cols.columns else ('Product' if 'Product' in df_cols.columns else df_cols.columns[0])

        query = f"""
            SELECT 
                {prod_col} AS Product_Name,
                COUNT(*) AS Total_Orders,
                SUM(CASE WHEN LOWER(CAST(Returned AS TEXT)) IN ('yes', '1', 'true') THEN 1 ELSE 0 END) AS Returned_Orders
            FROM sales
            GROUP BY {prod_col}
            HAVING Total_Orders > 0
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Calculate return rate percentage
        df['Return_Rate'] = (df['Returned_Orders'] / df['Total_Orders']) * 100
        df_top = df.sort_values(by='Return_Rate', ascending=False).head(10)

        return jsonify({
            "products": df_top['Product_Name'].tolist(),
            "return_rates": [round(val, 2) for val in df_top['Return_Rate'].tolist()],
            "total_orders": df_top['Total_Orders'].tolist(),
            "returned_orders": df_top['Returned_Orders'].tolist()
        })
    except Exception as e:
        print(f"Top Return Products API Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)