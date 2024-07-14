# Inventory Management using GenAI

This project showcases an innovative approach to inventory management by leveraging Generative AI capabilities. It combines a Streamlit web application with a SQLite database and Google's Gemini Pro AI model to provide an intuitive, AI-powered interface for managing product inventories.

## Features

- **Natural Language Queries**: Ask questions about your inventory in plain English.
- **AI-Powered SQL Generation**: Utilizes Google's Gemini Pro to convert natural language to SQL queries.
- **Interactive Dashboard**: Visualize inventory data with dynamic charts and graphs.
- **Inventory Modification**: Add, remove, or update products using natural language commands or Excel file uploads.
- **Bulk Data Processing**: Upload Excel files for batch updates to the inventory.
-**Automated Insights**: Products insights generated through the sales and trends 
-**Prediction of stocks**:Predicts the demand of the products 
-**Generate  Report**:Generates a whole report based the on the database 
## Files in the Repository

1. `main.py`: The core Streamlit application that handles the user interface and AI interactions.
2. `database.py`: Script to initialize and populate the SQLite database with sample product data.

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/inventory-management-using-GenAI.git
   cd inventory-management-using-GenAI
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Google API key:
   - Create a `.env` file in the project root.
   - Add your Google API key: `GOOGLE_API_KEY=your_api_key_here`

4. Initialize the database:
   ```
   python database.py
   ```

5. Run the Streamlit app:
   ```
   streamlit run main.py
   ```

## Usage

The application offers three main functionalities:

1. **Ask Questions**: Enter natural language queries about the inventory.
2. **View Dashboard**: Explore inventory statistics and visualizations.
3. **Modify Inventory**: Add, remove, or update products using AI-powered commands or Excel file uploads.

## Dependencies

- streamlit
- pandas
- sqlite3
- python-dotenv
- google-generativeai
- plotly
- faker

## Contributing

Contributions to improve the project are welcome. Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature.
3. Commit your changes.
4. Push to the branch.
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Gemini Pro for powering the AI capabilities.
- Streamlit for the web application framework.
