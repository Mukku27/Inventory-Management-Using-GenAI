import streamlit as st
import pandas as pd
import sqlite3
from dotenv import load_dotenv
import os
import google.generativeai as genai
import plotly.express as px
import pandasai
from pandasai import Agent

# Load environment variables
load_dotenv()

# Configure Google API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Get API key from environment variable
api_key = os.getenv("PANDASAI_API_KEY")

# Set API key for pandasai
os.environ["PANDASAI_API_KEY"] = api_key


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
    insights = Agent(df, description=description)
    insights = insights.chat(insights_prompt)
    return insights

# Function to predict stock needs
def predict_stock_needs(df):
    description = 'You are an expert in Data Analysis. Your main aim is to help non-technical people understand the insights and data analysis of the product inventory and product trends.'
    prediction_prompt = "Based on the current inventory data, predict which products are likely to run out of stock in the next month. Consider historical sales data if available."
    predictions = Agent(df, description=description)
    predictions = predictions.chat(prediction_prompt)
    return predictions

# Function to categorize a product
def categorize_product(df, product_name, product_description):
    description = 'You are an expert in Data Analysis. Your main aim is to help non-technical people understand the insights and data analysis of the product inventory and product trends.'
    categorization_prompt = f"Categorize this product: Name: {product_name}, Description: {product_description}"
    category = Agent(df, description=description)
    category = category.chat(categorization_prompt)
    return category

# Function to generate a comprehensive report
def generate_report(df):
    description = 'You are an expert in Data Analysis. Your main aim is to help non-technical people understand the insights and data analysis of the product inventory and product trends.'
    report_prompt = "Generate a comprehensive inventory report. Include total inventory value, top-selling products, low stock alerts, and any notable trends."
    report = Agent(df, description=description)
    report = report.chat(report_prompt)
    return report

# Defining your promptsimport streamlit as st
import pandas as pd
import sqlite3
from dotenv import load_dotenv
import os
import google.generativeai as genai
import plotly.express as px

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

# Defining your prompts
sql_prompt = """
You are an expert in converting English questions to SQL query!
The SQL database has the name PRODUCT and has the following columns NAME, CATEGORY, BRAND, PRICE, STOCK.

For example:
Example 1: How many products are in the inventory?
The SQL command will be something like this: SELECT COUNT(*) FROM PRODUCT;

Example 2: What are all the products in the Electronics category?
The SQL command will be something like this: SELECT * FROM PRODUCT where CATEGORY="Electronics";

The SQL code should not have ' in the beginning or end and 'sql' word in output.
"""

modification_prompt = """
You are an expert in converting English commands to SQL queries for database modification!
The SQL database has the name PRODUCT and has the following columns NAME, CATEGORY, BRAND, PRICE, STOCK.

For example:
Example 1: Add a new product named "Smart TV" in the Electronics category, brand Samsung, price $499, stock 50.
The SQL command will be something like this: INSERT INTO PRODUCT (NAME, CATEGORY, BRAND, PRICE, STOCK) VALUES ('Smart TV', 'Electronics', 'Samsung', 499, 50);

Example 2: Remove the product named "Smart TV".
The SQL command will be something like this: DELETE FROM PRODUCT WHERE NAME='Smart TV';

Example 3: Update the price of the product named "Smart TV" to $599.
The SQL command will be something like this: UPDATE PRODUCT SET PRICE=599 WHERE NAME='Smart TV';

The SQL code should not have ' in the beginning or end and 'sql' word in output.
"""

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

# Sidebar
st.sidebar.title("Menu")
st.sidebar.markdown("Navigate through the options:")
page = st.sidebar.selectbox("Choose a page", ["Ask Question About the Inventory", "Inventory Dashboard", "Modify Inventory"])

if page == "Ask Question About the Inventory":
    # Streamlit App for Text to SQL
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.markdown('<div class="title">Ask any question about Inventory</div>', unsafe_allow_html=True)
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    question = st.text_input("Enter your question about the inventory:")
    if st.button("Submit"):
        if question:
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="result-section">', unsafe_allow_html=True)
            st.write("Generating SQL query...")
            sql_query = generate_sql_query(sql_prompt, question)
            st.write(f"Generated SQL query: {sql_query}")
            
            st.write("Fetching data from the database...")
            db_path = 'product_inventory.db'
            try:
                results = read_sql_query(sql_query, db_path)
                if not results.empty:
                    st.write("Query Results:")
                    st.dataframe(results)
                else:
                    st.write("No results found.")
            except Exception as e:
                st.markdown('<div class="error">', unsafe_allow_html=True)
                st.write(f"Error: {e}")
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.write("Please enter a question.")
    else:
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Inventory Dashboard":
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.markdown('<div class="title">Inventory Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
    db_path = 'product_inventory.db'
    
    if st.button("Refresh Data"):
        st.rerun()
    
    try:
        conn = sqlite3.connect(db_path)
        st.write("Connected to database successfully!")
        st.write("Fetching data from the database...")
        sql = "SELECT * FROM PRODUCT"
        results = read_sql_query(sql, db_path)
        if not results.empty:
            st.write("Inventory Data:")
            st.dataframe(results)

            # Plotting insights
            st.write("Category Distribution:")
            category_count = results['CATEGORY'].value_counts().reset_index()
            category_count.columns = ['CATEGORY', 'COUNT']
            fig = px.bar(category_count, x='CATEGORY', y='COUNT', title="Category Distribution")
            st.plotly_chart(fig)

            st.write("Brand Distribution:")
            brand_count = results['BRAND'].value_counts().reset_index()
            brand_count.columns = ['BRAND', 'COUNT']
            fig = px.pie(brand_count, names='BRAND', values='COUNT', title="Brand Distribution")
            st.plotly_chart(fig)
            
        else:
            st.write("No data available.")
    except Exception as e:
        st.markdown('<div class="error">', unsafe_allow_html=True)
        st.write(f"Error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Modify Inventory":
    st.markdown('<div class="main">', unsafe_allow_html=True)
    st.markdown('<div class="title">Modify Inventory</div>', unsafe_allow_html=True)
    st.markdown('<div class="modification-section">', unsafe_allow_html=True)

    modification_type = st.radio("Select Modification Type", ["Add Product", "Remove Product", "Update Product"])

    if modification_type == "Add Product":
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        question = st.text_input("Enter your command to add a product:")
        if st.button("Submit Add Command"):
            if question:
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="result-section">', unsafe_allow_html=True)
                st.write("Generating SQL query...")
                sql_query = generate_sql_query(modification_prompt, question)
                st.write(f"Generated SQL query: {sql_query}")

                st.write("Executing SQL command...")
                db_path = 'product_inventory.db'
                try:
                    execute_sql_query(sql_query, db_path)
                    st.success("Product added successfully!")
                except Exception as e:
                    st.markdown('<div class="error">', unsafe_allow_html=True)
                    st.write(f"Error: {e}")
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.write("Please enter a command.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.markdown("Please ensure your Excel file has columns matching the database (NAME, CATEGORY, BRAND, PRICE, STOCK).")
        uploaded_file = st.file_uploader("Upload Excel file to add products", type=['xls', 'xlsx'])
        if uploaded_file:
            try:
                process_excel_file(uploaded_file, 'product_inventory.db', action="add")
                st.success("Data updated successfully!")
            except Exception as e:
                st.error(f"Error processing Excel file: {str(e)}")
        else:
            st.write("Please upload an Excel file.")
        st.markdown('</div>', unsafe_allow_html=True)

    elif modification_type == "Remove Product":
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        question = st.text_input("Enter your command to remove a product:")
        if st.button("Submit Remove Command"):
            if question:
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="result-section">', unsafe_allow_html=True)
                st.write("Generating SQL query...")
                sql_query = generate_sql_query(modification_prompt, question)
                st.write(f"Generated SQL query: {sql_query}")

                st.write("Executing SQL command...")
                db_path = 'product_inventory.db'
                try:
                    execute_sql_query(sql_query, db_path)
                    st.success("Product removed successfully!")
                except Exception as e:
                    st.markdown('<div class="error">', unsafe_allow_html=True)
                    st.write(f"Error: {e}")
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.write("Please enter a command.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.markdown("Please ensure your Excel file has columns matching the database (NAME, CATEGORY, BRAND, PRICE, STOCK).")
        uploaded_file = st.file_uploader("Upload Excel file to remove products", type=['xls', 'xlsx'])
        if uploaded_file:
            try:
                process_excel_file(uploaded_file, 'product_inventory.db', action="remove")
                st.success("Data updated successfully!")
            except Exception as e:
                st.error(f"Error processing Excel file: {str(e)}")
        else:
            st.write("Please upload an Excel file.")
        st.markdown('</div>', unsafe_allow_html=True)

    elif modification_type == "Update Product":
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        question = st.text_input("Enter your command to update a product:")
        if st.button("Submit Update Command"):
            if question:
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="result-section">', unsafe_allow_html=True)
                st.write("Generating SQL query...")
                sql_query = generate_sql_query(modification_prompt, question)
                st.write(f"Generated SQL query: {sql_query}")

                st.write("Executing SQL command...")
                db_path = 'product_inventory.db'
                try:
                    execute_sql_query(sql_query, db_path)
                    st.success("Product updated successfully!")
                except Exception as e:
                    st.markdown('<div class="error">', unsafe_allow_html=True)
                    st.write(f"Error: {e}")
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.write("Please enter a command.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.markdown("Please ensure your Excel file has columns matching the database (NAME, CATEGORY, BRAND, PRICE, STOCK).")
        uploaded_file = st.file_uploader("Upload Excel file to update products", type=['xls', 'xlsx'])
        if uploaded_file:
            try:
                process_excel_file(uploaded_file, 'product_inventory.db', action="modify")
                st.success("Data updated successfully!")
            except Exception as e:
                st.error(f"Error processing Excel file: {str(e)}")
        else:
            st.write("Please upload an Excel file.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

sql_prompt = """
You are an expert in converting English questions to SQL query!
The SQL database has the name PRODUCT and has the following columns NAME, CATEGORY, BRAND, PRICE, STOCK.

For example:
Example 1: How many products are in the inventory?
The SQL command will be something like this: SELECT COUNT(*) FROM PRODUCT;

Example 2: What are all the products in the Electronics category?
The SQL command will be something like this: SELECT * FROM PRODUCT where CATEGORY="Electronics";

The SQL code should not have ' in the beginning or end and 'sql' word in output.
"""

modification_prompt = """
You are an expert in converting English commands to SQL queries for database modification!
The SQL database has the name PRODUCT and has the following columns NAME, CATEGORY, BRAND, PRICE, STOCK.

For example:
Example 1: Add a new product named "Smart TV" in the Electronics category, brand Samsung, price $499, stock 50.
The SQL command will be something like this: INSERT INTO PRODUCT (NAME, CATEGORY, BRAND, PRICE, STOCK) VALUES ('Smart TV', 'Electronics', 'Samsung', 499, 50);

Example 2: Remove the product named "Smart TV".
The SQL command will be something like this: DELETE FROM PRODUCT WHERE NAME='Smart TV';

Example 3: Update the price of the product named "Smart TV" to $599.
The SQL command will be something like this: UPDATE PRODUCT SET PRICE=599 WHERE NAME='Smart TV';

The SQL code should not have ' in the beginning or end and 'sql' word in output.
"""

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
query = "SELECT * FROM PRODUCT"
df = read_sql_query(query, db_path)

if not df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        total_products = df['NAME'].nunique()
        st.markdown('<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Total Products</div></div>'.format(total_products), unsafe_allow_html=True)
    with col2:
        total_stock = df['STOCK'].sum()
        st.markdown('<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Total Stock</div></div>'.format(total_stock), unsafe_allow_html=True)
    with col3:
        total_value = df['PRICE'].sum()
        st.markdown('<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Total Value ($)</div></div>'.format(total_value), unsafe_allow_html=True)

    # Inventory Insights
    st.markdown('<h2>Inventory Insights</h2>', unsafe_allow_html=True)
    insights = generate_insights(df)
    st.write(insights)

    # Stock Prediction
    st.markdown('<h2>Stock Prediction</h2>', unsafe_allow_html=True)
    stock_predictions = predict_stock_needs(df)
    st.write(stock_predictions)

    # Categorize Product
    st.markdown('<h2>Categorize Product</h2>', unsafe_allow_html=True)
    product_name = st.text_input("Product Name")
    product_description = st.text_input("Product Description")
    if st.button("Categorize"):
        category = categorize_product(df, product_name, product_description)
        st.write(category)

    # Comprehensive Report
    st.markdown('<h2>Comprehensive Report</h2>', unsafe_allow_html=True)
    report = generate_report(df)
    st.write(report)

    # Inventory Data
    st.markdown('<h2>Inventory Data</h2>', unsafe_allow_html=True)
    st.dataframe(df)
else:
    st.markdown('<div class="error">No data available in the inventory. Please upload an Excel file to populate the database.</div>', unsafe_allow_html=True)

# Question to SQL Query Section
st.markdown('<div class="input-section"><h2>Ask Inventory Questions</h2>', unsafe_allow_html=True)
question = st.text_input("Enter your question about the inventory:")
if st.button("Get Answer"):
    sql_query = generate_sql_query(sql_prompt, question)
    if sql_query:
        result_df = read_sql_query(sql_query, db_path)
        st.write(result_df)
    else:
        st.write("Could not generate a valid SQL query from the question.")

# Modify Inventory Section
st.markdown('<div class="modification-section"><h2>Modify Inventory</h2>', unsafe_allow_html=True)
modification_command = st.text_input("Enter your modification command (e.g., Add, Update, Remove):")
if st.button("Execute"):
    sql_query = generate_sql_query(modification_prompt, modification_command)
    if sql_query:
        execute_sql_query(sql_query, db_path)
        st.write("Modification executed successfully.")
    else:
        st.write("Could not generate a valid SQL query from the command.")

# Upload Excel File Section
st.markdown('<div class="upload-section"><h2>Upload Excel File</h2>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
if uploaded_file is not None:
    df_uploaded = pd.read_excel(uploaded_file)
    st.dataframe(df_uploaded)
    action = st.selectbox("Select Action", ["add", "modify", "remove"])
    if st.button("Process File"):
        process_excel_file(uploaded_file, db_path, action)
        st.write("File processed successfully.")
