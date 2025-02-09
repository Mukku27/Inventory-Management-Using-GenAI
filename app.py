"""
app.py

The main entry point for the Inventory Management application. This module initializes the Streamlit UI,
handles user inputs, and calls functions from other modules to execute the core logic.
"""

import streamlit as st
import os
from config import GOOGLE_API_KEY, PANDASAI_API_KEY  # ensure configuration is loaded
from utils import read_sql_query
from prompt import generate_sql_query
from excel_processing import process_excel_file
from analytics import generate_insights, predict_stock_needs, categorize_product, generate_report
from pandasai import Agent

# Set up Streamlit page configuration
st.set_page_config(
    page_title="Inventory Management Using GenAI",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark theme styling
st.markdown("""
<style>
    body {
        color: #fff;
        background-color: #0e1117;
    }
    .main {
        background-color: #1a1b21;
        padding: 20px;
        border-radius: 10px;
    }
    .title {
        color: #1DB954;
        text-align: center;
        font-size: 2.5em;
    }
    .input-section, .dashboard-section, .modification-section, .upload-section {
        background-color: #2c2f36;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .result-section {
        background-color: #2c2f36;
        padding: 15px;
        border-radius: 10px;
    }
    .error {
        background-color: #2c2f36;
        padding: 15px;
        border-radius: 10px;
        color: #d32f2f;
    }
    .stTextInput>div>div>input {
        background-color: #3c404a;
        color: #fff;
        border-radius: 5px;
    }
    .stButton>button {
        background-color: #1DB954;
        color: #fff;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #1ed760;
        color: #fff;
    }
    .metric-card {
        background-color: #3c404a;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #1DB954;
    }
    .metric-label {
        font-size: 0.9em;
        color: #a0a0a0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title">Inventory Management Using GenAI</h1>', unsafe_allow_html=True)

# --------------------------
# Dashboard Metrics Section
# --------------------------
st.markdown('<h2>Inventory Dashboard</h2>', unsafe_allow_html=True)
db_path = 'inventory.db'
query = "SELECT COUNT(*) as product_count, SUM(price * quantity) as total_inventory_value FROM PRODUCT"
df = read_sql_query(query, db_path)
product_count = df['product_count'].values[0]
total_inventory_value = df['total_inventory_value'].values[0]

col1, col2 = st.columns(2)
with col1:
    st.markdown(
        '<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Total Products</div></div>'.format(product_count),
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        '<div class="metric-card"><div class="metric-value">${:,.2f}</div><div class="metric-label">Total Inventory Value</div></div>'.format(total_inventory_value),
        unsafe_allow_html=True
    )

# --------------------------
# Plotting Section
# --------------------------
st.markdown('<h2>Plotting Parameters</h2>', unsafe_allow_html=True)
user_prompt = st.text_area("Enter your plot prompt:")

if st.button("Plot Parameters"):
    if user_prompt:
        df_full = read_sql_query("SELECT * FROM PRODUCT", db_path)
        agent = Agent()
        response = agent.chat({"user_prompt": user_prompt, "df": df_full})
        st.pyplot(response)
    else:
        st.error("Please provide a prompt for plotting.")

# --------------------------
# SQL Query Section
# --------------------------
st.markdown('<h2>SQL Query Input</h2>', unsafe_allow_html=True)
question = st.text_area("Enter your query in natural language:")

if st.button("Generate SQL Query"):
    if question:
        db_description = "Product table schema: PRODUCT (ID INTEGER PRIMARY KEY AUTOINCREMENT, NAME TEXT, QUANTITY INTEGER, PRICE REAL, CATEGORY TEXT)"
        sql_query = generate_sql_query(db_description, question)
        st.write("Generated SQL Query:", sql_query)
        try:
            result_df = read_sql_query(sql_query, db_path)
            st.write(result_df)
        except Exception as e:
            st.error(f"Error executing SQL query: {e}")
    else:
        st.error("Please enter a query.")

# --------------------------
# Excel File Processing Section
# --------------------------
st.markdown('<h2>Upload Excel File</h2>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
action = st.selectbox("Select Action", ["add", "remove", "modify"])

if st.button("Process Excel File"):
    if uploaded_file:
        process_excel_file(uploaded_file, db_path, action)
        st.success(f"Successfully processed the Excel file for {action} action.")
    else:
        st.error("Please upload an Excel file.")

# --------------------------
# Inventory Insights Section
# --------------------------
st.markdown('<h2>Generate Inventory Insights</h2>', unsafe_allow_html=True)
if st.button("Generate Insights"):
    df_full = read_sql_query("SELECT * FROM PRODUCT", db_path)
    insights = generate_insights(df_full)
    st.write("Inventory Insights:", insights)

# --------------------------
# Stock Prediction Section
# --------------------------
st.markdown('<h2>Predict Stock Needs</h2>', unsafe_allow_html=True)
if st.button("Predict Stock Needs"):
    df_full = read_sql_query("SELECT * FROM PRODUCT", db_path)
    predictions = predict_stock_needs(df_full)
    st.write("Stock Predictions:", predictions)

# --------------------------
# Product Categorization Section
# --------------------------
st.markdown('<h2>Categorize Product</h2>', unsafe_allow_html=True)
product_name = st.text_input("Enter the product name:")
product_description = st.text_area("Enter the product description:")

if st.button("Categorize Product"):
    if product_name and product_description:
        df_full = read_sql_query("SELECT * FROM PRODUCT", db_path)
        category = categorize_product(df_full, product_name, product_description)
        st.write("Product Category:", category)
    else:
        st.error("Please provide both product name and description.")

# --------------------------
# Inventory Report Section
# --------------------------
st.markdown('<h2>Generate Inventory Report</h2>', unsafe_allow_html=True)
if st.button("Generate Report"):
    df_full = read_sql_query("SELECT * FROM PRODUCT", db_path)
    report = generate_report(df_full)
    st.write("Inventory Report:", report)
