import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime

class SheetHandler:
    def __init__(self):
        """
        Initializes the Google Sheets client using credentials from Streamlit secrets.
        """
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = None
        self.sheet = None
        self.connect()

    def connect(self):
        """
        Connects to Google Sheets using the service account JSON in secrets.
        """
        try:
            # Construct credentials from the secrets dictionary
            # We expect the secrets to have a [gcp_service_account] section
            # or simply be flattened. The standard way for Streamlit secrets with GSheets
            # often involves putting the whole JSON content into the secrets.
            
            # Assuming the user will paste the JSON content into secrets.toml 
            # under a key named "gcp_service_account"
            
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
                credentials = Credentials.from_service_account_info(
                    creds_dict, scopes=self.scope
                )
                self.client = gspread.authorize(credentials)
            else:
                st.error("Missing 'gcp_service_account' in secrets.toml")

        except Exception as e:
            st.error(f"Google Sheets Connection Error: {e}")

    def append_data(self, sheet_url, data_dict):
        """
        Appends a row to the 'Stock_In' worksheet.
        Columns: A=Date, B=Ingredient, C=Manufacturer, D=Quantity
        """
        if not self.client:
            st.error("Not connected to Google Sheets.")
            return False

        try:
            # Open the spreadsheet
            if sheet_url.startswith("https://"):
                sh = self.client.open_by_url(sheet_url)
            else:
                sh = self.client.open(sheet_url)
                
            # Select 'Stock_In' worksheet
            try:
                worksheet = sh.worksheet("Stock_In")
            except gspread.WorksheetNotFound:
                # If Stock_In doesn't exist, create it
                worksheet = sh.add_worksheet(title="Stock_In", rows=100, cols=20)
                # Add headers if new
                worksheet.append_row(["Date", "Ingredient Name", "Manufacturer", "Quantity (g)"])
            
            # Prepare the row
            # Column A: Empty (for formula)
            # Column B: Ingredient
            # Column C: Manufacturer
            # Column D: Quantity
            # Process quantity to be a number
            raw_qty = data_dict.get("quantity_g", "")
            qty_val = raw_qty
            try:
                # Remove 'g', spaces, replace comma with dot
                if raw_qty:
                    clean_qty = str(raw_qty).lower().replace('g', '').replace('kg', '').replace('ml', '').replace('l', '').replace(' ', '').replace(',', '.')
                    val = float(clean_qty)
                    # Convert to int if it's a whole number (e.g. 500.0 -> 500)
                    if val.is_integer():
                        qty_val = int(val)
                    else:
                        qty_val = val
            except ValueError:
                pass # Keep as string if conversion fails

            row = [
                "",  # Column A left empty for formula
                data_dict.get("ingredient", ""),
                data_dict.get("manufacturer", ""),
                qty_val
            ]
            
            worksheet.append_row(row)
            return True

        except Exception as e:
            st.error(f"Error saving to Sheet: {e}")
            return False

    def get_data(self, sheet_url):
        """
        Fetches all data from 'Stock_In' to display in the app.
        Returns a list of lists (rows).
        """
        if not self.client:
            return []
            
        try:
            if sheet_url.startswith("https://"):
                sh = self.client.open_by_url(sheet_url)
            else:
                sh = self.client.open(sheet_url)
            
            worksheet = sh.worksheet("Stock_In")
            return worksheet.get_all_values()
        except Exception:
            return []

    def delete_row(self, sheet_url, row_index):
        """
        Deletes a specific row from 'Stock_In' by its 1-based index.
        """
        if not self.client:
            return False
            
        try:
            if sheet_url.startswith("https://"):
                sh = self.client.open_by_url(sheet_url)
            else:
                sh = self.client.open(sheet_url)
            
            worksheet = sh.worksheet("Stock_In")
            worksheet.delete_rows(row_index)
            return True
        except Exception as e:
            st.error(f"Error deleting row: {e}")
            return False

    def batch_append_data(self, sheet_url, data_list):
        """
        Appends multiple rows to the 'Stock_In' worksheet at once.
        
        Args:
            sheet_url (str): The URL of the Google Sheet.
            data_list (list): A list of dictionaries containing 'ingredient', 'manufacturer', 'quantity_g'.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.client:
            st.error("Not connected to Google Sheets.")
            return False

        try:
            # Open the spreadsheet
            if sheet_url.startswith("https://"):
                sh = self.client.open_by_url(sheet_url)
            else:
                sh = self.client.open(sheet_url)
                
            # Select 'Stock_In' worksheet
            try:
                worksheet = sh.worksheet("Stock_In")
            except gspread.WorksheetNotFound:
                worksheet = sh.add_worksheet(title="Stock_In", rows=100, cols=20)
                worksheet.append_row(["Date", "Ingredient Name", "Manufacturer", "Quantity (g)"])
            
            rows_to_append = []
            for data_dict in data_list:
                # Process quantity
                raw_qty = data_dict.get("quantity_g", "")
                qty_val = raw_qty
                try:
                    if raw_qty:
                        clean_qty = str(raw_qty).lower().replace('g', '').replace('kg', '').replace('ml', '').replace('l', '').replace(' ', '').replace(',', '.')
                        val = float(clean_qty)
                        if val.is_integer():
                            qty_val = int(val)
                        else:
                            qty_val = val
                except ValueError:
                    pass

                row = [
                    "",  # Column A left empty for formula
                    data_dict.get("ingredient", ""),
                    data_dict.get("manufacturer", ""),
                    qty_val
                ]
                rows_to_append.append(row)
            
            if rows_to_append:
                worksheet.append_rows(rows_to_append)
            return True

        except Exception as e:
            st.error(f"Error saving batch to Sheet: {e}")
            return False
