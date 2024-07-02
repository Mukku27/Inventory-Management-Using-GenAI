import sqlite3
import random
from faker import Faker

# Connect to the SQLite database
connection = sqlite3.connect("product_inventory.db")
cursor = connection.cursor()

# Drop the existing PRODUCT table if it exists
cursor.execute("DROP TABLE IF EXISTS PRODUCT")

# Create the PRODUCT table
table_info = """
CREATE TABLE IF NOT EXISTS PRODUCT (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    NAME VARCHAR(100),
    CATEGORY VARCHAR(50),
    BRAND VARCHAR(50),
    PRICE REAL,
    STOCK INTEGER,
    SIZE VARCHAR(20),
    COLOR VARCHAR(20),
    WEIGHT REAL,
    SPECIFICATIONS TEXT
);
"""
cursor.execute(table_info)

# Generate sample data using Faker
fake = Faker()

def generate_product_name():
    adjectives = ['Premium', 'Deluxe', 'Advanced', 'Smart', 'Eco-friendly', 'Compact', 'Portable', 'Professional']
    nouns = ['Device', 'Gadget', 'Tool', 'Appliance', 'System', 'Kit', 'Set', 'Solution']
    return f"{random.choice(adjectives)} {fake.word().capitalize()} {random.choice(nouns)}"

def generate_product_data(num_products):
    product_data = []
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports & Outdoors', 'Books', 'Toys', 'Beauty', 'Food & Beverage']
    sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'N/A']
    
    for _ in range(num_products):
        name = generate_product_name()
        category = random.choice(categories)
        brand = fake.company()
        price = round(random.uniform(1.0, 1000.0), 2)
        stock = random.randint(0, 1000)
        size = random.choice(sizes)
        color = fake.color_name()
        weight = round(random.uniform(0.1, 50.0), 2)
        specifications = fake.text(max_nb_chars=200)
        
        product_data.append((name, category, brand, price, stock, size, color, weight, specifications))
    return product_data

# Insert sample data into the PRODUCT table
num_products = 10000  # Generating 10,000 products
product_data = generate_product_data(num_products)

# Insert the generated data into the table
cursor.executemany("""
    INSERT INTO PRODUCT (NAME, CATEGORY, BRAND, PRICE, STOCK, SIZE, COLOR, WEIGHT, SPECIFICATIONS) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
""", product_data)

# Commit the changes and close the connection
connection.commit()
connection.close()

# Retrieve and print a few rows from the PRODUCT table to verify the data
re_connection = sqlite3.connect("product_inventory.db")
re_cursor = re_connection.cursor()

select_data = "SELECT * FROM PRODUCT LIMIT 10;"
re_cursor.execute(select_data)

# Fetch all rows from the result
rows = re_cursor.fetchall()

# Print each row
for row in rows:
    print(row)

# Close the re-established connection
re_connection.close()

print(f"\nSuccessfully created a product inventory database with {num_products} products.")