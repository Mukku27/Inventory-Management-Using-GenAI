# Inventory Management using GenAI

This project demonstrates an innovative approach to inventory management leveraging Generative AI.  It integrates a Streamlit web application, a SQLite database, and Google's Gemini Pro AI model for an intuitive, AI-powered inventory management interface.

## Features

- **Natural Language Queries:**  Ask questions about your inventory using plain English.
- **AI-Powered SQL Generation:**  Converts natural language queries into SQL using Google's Gemini Pro.
- **Interactive Dashboard:** Visualizes inventory data with dynamic charts and graphs.
- **Inventory Modification:** Add, remove, or update products via natural language commands or Excel file uploads.
- **Bulk Data Processing:** Upload Excel files for batch inventory updates.
- **Automated Insights:** Generates insights based on sales and trends.
- **Stock Prediction:** Predicts product demand using AI.
- **Report Generation:** Creates comprehensive reports based on the database.
- **Customizable Plotting:** Allows users to generate plots based on their specified parameters, enabling non-technical users to perform basic data analysis.


## Files in the Repository

1. `app.py`: The main Streamlit application handling user interface and AI interactions.
2. `database.py`:  Initializes and populates the SQLite database with sample product data.
3. `analytics.py`: Contains functions for AI-powered inventory analysis (insights, predictions, categorization, reporting).
4. `excel_processing.py`: Handles processing of uploaded Excel files for database updates.
5. `config.py`: Loads environment variables and configures API keys.
6. `prompt.py`: (Assumed file - not present in provided code) Contains functions related to prompt engineering for the AI models.
7. `utils.py`: (Assumed file - not present in provided code) Contains utility functions used throughout the application.


## Setup and Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd inventory-management-using-GenAI
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys:**
   - Create a `.env` file in the project root.
   - Add your Google Cloud API key: `GOOGLE_API_KEY=your_api_key_here`
   - Obtain a PandasAI API key from [www.pandabi.com](www.pandabi.com) and add it: `PANDASAI_API_KEY=your_api_key_here`

4. **Initialize the database:**
   ```bash
   python database.py
   ```

5. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

## Usage

The application provides these main functionalities:

1. **Ask Questions:** Input natural language queries to retrieve inventory information.
2. **View Dashboard:** Access interactive dashboards displaying key inventory metrics.
3. **Modify Inventory:**  Add, remove, or modify products using natural language or Excel file uploads.
4. **Generate Insights/Predictions/Reports:** Utilize AI-powered functions to gain deeper insights into your inventory.
5. **Plot Parameters:** Create custom plots to visualize your data.


## Dependencies

- streamlit
- pandas
- sqlite3
- python-dotenv
- google-generativeai
- pandasai
- plotly
- faker


## Contributing

Contributions are welcome!  Follow these steps:

1. Fork the repository.
2. Create a new branch for your feature.
3. Commit your changes.
4. Push to the branch.
5. Create a pull request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

