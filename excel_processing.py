"""
excel_processing.py

This module handles the processing of uploaded Excel files and updates the database accordingly.
"""

import pandas as pd
import sqlite3
import streamlit as st
from utils import add_column_to_db, map_columns
from prompt import get_gemini_response

def process_excel_file(uploaded_file, db_path, action):
    """
    Processes an uploaded Excel file to update the PRODUCT table in the database.
    
    Args:
        uploaded_file: The uploaded Excel file.
        db_path (str): The path to the database.
        action (str): The action to perform ("add", "remove", or "modify").
    """
    df = pd.read_excel(uploaded_file)
    st.write("Column names in the uploaded file:", df.columns.tolist())

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(PRODUCT)")
    existing_columns = [info[1] for info in cursor.fetchall()]

    # Map Excel columns to database columns using the Gemini Pro model
    column_mappings = map_columns(df.columns, existing_columns, get_gemini_response)

    for excel_col, db_col in column_mappings.items():
        if db_col not in existing_columns:
            add_column_to_db(db_path, db_col)
            existing_columns.append(db_col)

    # Process each row in the Excel file
    for index, row in df.iterrows():
        mapped_row = {column_mappings[col]: value for col, value in row.items()}

        if action == "remove":
            cursor.execute("DELETE FROM PRODUCT WHERE NAME=?", (mapped_row.get('NAME'),))
        elif action == "modify":
            set_clause = ", ".join([f"{col}=?" for col in mapped_row.keys()])
            values = tuple(mapped_row.values())
            cursor.execute(f"UPDATE PRODUCT SET {set_clause} WHERE NAME=?", values + (mapped_row.get('NAME'),))
        else:  # add action (or update if product exists)
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
