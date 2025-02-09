"""
analytics.py

This module contains functions to analyze inventory data using AI to generate insights, predict stock needs,
categorize products, and generate comprehensive reports.
"""

import google.generativeai as genai
from pandasai import Agent

def generate_insights(df):
    """
    Generates key insights from the inventory data.
    
    Args:
        df (pd.DataFrame): The inventory data.
    
    Returns:
        str: Generated insights.
    """
    description = (
        "You are an expert in Data Analysis. Your main aim is to help non-technical people understand "
        "the insights and data analysis of the product inventory and product trends."
    )
    insights_prompt = "Analyze this inventory data and provide key insights about stock levels, popular categories, and pricing trends."
    insights_agent = genai.Agent(df, description=description)
    insights = insights_agent.chat(insights_prompt)
    return insights

def predict_stock_needs(df):
    """
    Predicts which products are likely to run out of stock in the next month.
    
    Args:
        df (pd.DataFrame): The inventory data.
    
    Returns:
        str: Stock predictions.
    """
    description = (
        "You are an expert in Data Analysis. Your main aim is to help non-technical people understand "
        "the insights and data analysis of the product inventory and product trends."
    )
    prediction_prompt = "Based on the current inventory data, predict which products are likely to run out of stock in the next month. Consider historical sales data if available."
    predictions_agent = genai.Agent(df, description=description)
    predictions = predictions_agent.chat(prediction_prompt)
    return predictions

def categorize_product(df, product_name, product_description):
    """
    Categorizes a product based on its name and description.
    
    Args:
        df (pd.DataFrame): The inventory data.
        product_name (str): The product name.
        product_description (str): The product description.
    
    Returns:
        str: The category of the product.
    """
    description = (
        "You are an expert in Data Analysis. Your main aim is to help non-technical people understand "
        "the insights and data analysis of the product inventory and product trends."
    )
    categorization_prompt = f"Categorize this product: Name: {product_name}, Description: {product_description}"
    category_agent = genai.Agent(df, description=description)
    category = category_agent.chat(categorization_prompt)
    return category

def generate_report(df):
    """
    Generates a comprehensive inventory report.
    
    Args:
        df (pd.DataFrame): The inventory data.
    
    Returns:
        str: The inventory report.
    """
    description = (
        "You are an expert in Data Analysis. Your main aim is to help non-technical people understand "
        "the insights and data analysis of the product inventory and product trends."
    )
    report_prompt = (
        "Generate a comprehensive inventory report. Include total inventory value, top-selling products, "
        "low stock alerts, and any notable trends."
    )
    report_agent = genai.Agent(df, description=description)
    report = report_agent.chat(report_prompt)
    return report
