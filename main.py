import streamlit as st
import pandas as pd
import sqlite3
from dotenv import load_dotenv
import os
import google.generativeai as genai
from pandasai import Agent
from pandasai.skills import skill

# Load environment variables
load_dotenv()

# Configure Google API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Google Gemini Pro model
def get_gemini_response(prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt])
    return response.text

# Function to generate SQL query using prompt and question
def generate_sql_query(prompt, question):
    full_prompt = f"{prompt}\n{question}"
    sql_query = get_gemini_response(full_prompt).strip()
    return sql_query

# Function to execute an SQL query on the database
def execute_sql_query(sql, db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    conn.close()

# Function to retrieve query results from the database 
def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

# Function to add a column to the database
def add_column_to_db(db_path, column_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"ALTER TABLE PRODUCT ADD COLUMN {column_name} TEXT")
    conn.commit()
    conn.close()

# Function to map Excel columns to database columns using Gemini Pro API
def map_columns(excel_columns, db_columns):
    mappings = {}
    for excel_col in excel_columns:
        prompt = f"Find the best match for the column '{excel_col}' from the following options: {', '.join(db_columns)}"
        best_match = get_gemini_response(prompt).strip()
        mappings[excel_col] = best_match
    return mappings

# Function to process the Excel file and update the database
def process_excel_file(uploaded_file, db_path, action):
    df = pd.read_excel(uploaded_file)
    st.write("Column names in the uploaded file:", df.columns.tolist())

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(PRODUCT)")
    existing_columns = [info[1] for info in cursor.fetchall()]

    column_mappings = map_columns(df.columns, existing_columns)

    for excel_col, db_col in column_mappings.items():
        if db_col not in existing_columns:
            add_column_to_db(db_path, db_col)
            existing_columns.append(db_col)

    for index, row in df.iterrows():
        mapped_row = {column_mappings[col]: value for col, value in row.items()}
        
        if action == "remove":
            cursor.execute("DELETE FROM PRODUCT WHERE NAME=?", (mapped_row.get('NAME'),))
        
        elif action == "modify":
            set_clause = ", ".join([f"{col}=?" for col in mapped_row.keys()])
            values = tuple(mapped_row.values())
            cursor.execute(f"UPDATE PRODUCT SET {set_clause} WHERE NAME=?", values + (mapped_row.get('NAME'),))
        
        else:
            cursor.execute("SELECT * FROM PRODUCT WHERE NAME=?", (mapped_row.get('NAME'),))
            existing_product = cursor.fetchone()
            if existing_product:
                set_clause = ", ".join([f"{col}=?" for col in mapped_row.keys()])
                values = tuple(mapped_row.values())
                cursor.execute(f"UPDATE PRODUCT SET {set_clause} WHERE NAME=?", values + (mapped_row.get('NAME'),))
            else:
                columns = ", ".join(mapped_row.keys())
                placeholders = ", ".join(["?" for _ in mapped_row])
                values = tuple(mapped_row.values())
                cursor.execute(f"INSERT INTO PRODUCT ({columns}) VALUES ({placeholders})", values)

    conn.commit()
    conn.close()

# Function to generate insights from the data
def generate_insights(df):
    description = 'You are an expert in Data Analysis. Your main aim is to help non-technical people understand the insights and data analysis of the product inventory and product trends.'
    insights_prompt = "Analyze this inventory data and provide key insights about stock levels, popular categories, and pricing trends."
    insights = genai.Agent(df, description=description)
    insights = insights.chat(insights_prompt)
    return insights

# Function to predict stock needs
def predict_stock_needs(df):
    description = 'You are an expert in Data Analysis. Your main aim is to help non-technical people understand the insights and data analysis of the product inventory and product trends.'
    prediction_prompt = "Based on the current inventory data, predict which products are likely to run out of stock in the next month. Consider historical sales data if available."
    predictions = genai.Agent(df, description=description)
    predictions = predictions.chat(prediction_prompt)
    return predictions

# Function to categorize a product
def categorize_product(df, product_name, product_description):
    description = 'You are an expert in Data Analysis. Your main aim is to help non-technical people understand the insights and data analysis of the product inventory and product trends.'
    categorization_prompt = f"Categorize this product: Name: {product_name}, Description: {product_description}"
    category = genai.Agent(df, description=description)
    category = category.chat(categorization_prompt)
    return category

# Function to generate a comprehensive report
def generate_report(df):
    description = 'You are an expert in Data Analysis. Your main aim is to help non-technical people understand the insights and data analysis of the product inventory and product trends.'
    report_prompt = "Generate a comprehensive inventory report. Include total inventory value, top-selling products, low stock alerts, and any notable trends."
    report = genai.Agent(df, description=description)
    report = report.chat(report_prompt)
    return report

# Function doc string to give more context to the model for use this skill
@skill
def plot_parameter(parameter1, parameter2, df):
    """
    Displays a bar chart comparing two parameters from the dataframe.
    Args:
        parameter1 (str): The first parameter to plot.
        parameter2 (str): The second parameter to plot.
        df (pd.DataFrame): The dataframe containing the data.
    """
    # plot bars
    import matplotlib.pyplot as plt

    plt.bar(df[parameter1], df[parameter2])
    plt.xlabel(parameter1)
    plt.ylabel(parameter2)
    plt.title(f"{parameter1} vs {parameter2}")
    plt.xticks(rotation=45)
    plt.show()

# By default, unless you choose a different LLM, it will use BambooLLM.
# You can get your free API key signing up at https://pandabi.ai (you can also configure it in your .env file)
os.environ["PANDASAI_API_KEY"] = os.getenv("PANDASAI_API_KEY")

# Streamlit Page Configuration
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

# Streamlit App
st.markdown('<h1 class="title">Inventory Management Using GenAI</h1>', unsafe_allow_html=True)

# Dashboard Metrics
st.markdown('<h2>Inventory Dashboard</h2>', unsafe_allow_html=True)
db_path = 'inventory.db'
query = "SELECT COUNT(*) as product_count, SUM(price * quantity) as total_inventory_value FROM PRODUCT"
df = read_sql_query(query, db_path)
product_count = df['product_count'].values[0]
total_inventory_value = df['total_inventory_value'].values[0]

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Total Products</div></div>'.format(product_count), unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><div class="metric-value">${:,.2f}</div><div class="metric-label">Total Inventory Value</div></div>'.format(total_inventory_value), unsafe_allow_html=True)

# User Input for Plotting
st.markdown('<h2>Plotting Parameters</h2>', unsafe_allow_html=True)
user_prompt = st.text_area("Enter your plot prompt:")

if st.button("Plot Parameters"):
    if user_prompt:
        df = read_sql_query("SELECT * FROM PRODUCT", db_path)
        agent = Agent()
        response = agent.chat({"user_prompt": user_prompt, "df": df})
        st.pyplot(response)
    else:
        st.error("Please provide a prompt for plotting.")

# User Input for SQL Commands
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

# User Input for Excel File Processing
st.markdown('<h2>Upload Excel File</h2>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
action = st.selectbox("Select Action", ["add", "remove", "modify"])

if st.button("Process Excel File"):
    if uploaded_file:
        process_excel_file(uploaded_file, db_path, action)
        st.success(f"Successfully processed the Excel file for {action} action.")
    else:
        st.error("Please upload an Excel file.")

# User Input for Inventory Insights
st.markdown('<h2>Generate Inventory Insights</h2>', unsafe_allow_html=True)
if st.button("Generate Insights"):
    df = read_sql_query("SELECT * FROM PRODUCT", db_path)
    insights = generate_insights(df)
    st.write("Inventory Insights:", insights)

# User Input for Stock Predictions
st.markdown('<h2>Predict Stock Needs</h2>', unsafe_allow_html=True)
if st.button("Predict Stock Needs"):
    df = read_sql_query("SELECT * FROM PRODUCT", db_path)
    predictions = predict_stock_needs(df)
    st.write("Stock Predictions:", predictions)

# User Input for Product Categorization
st.markdown('<h2>Categorize Product</h2>', unsafe_allow_html=True)
product_name = st.text_input("Enter the product name:")
product_description = st.text_area("Enter the product description:")

if st.button("Categorize Product"):
    if product_name and product_description:
        df = read_sql_query("SELECT * FROM PRODUCT", db_path)
        category = categorize_product(df, product_name, product_description)
        st.write("Product Category:", category)
    else:
        st.error("Please provide both product name and description.")

# User Input for Inventory Report
st.markdown('<h2>Generate Inventory Report</h2>', unsafe_allow_html=True)
if st.button("Generate Report"):
    df = read_sql_query("SELECT * FROM PRODUCT", db_path)
    report = generate_report(df)
    st.write("Inventory Report:", report)
