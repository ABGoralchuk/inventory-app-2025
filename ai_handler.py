import google.generativeai as genai
import json
import os
import streamlit as st
from PIL import Image
import io

class GeminiHandler:
    def __init__(self):
        """
        Initializes the Gemini API client using the key from Streamlit secrets.
        """
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            st.error(f"Error configuring Gemini API: {e}. Please check your .streamlit/secrets.toml file.")
            self.model = None

    def extract_data(self, image_bytes):
        """
        Sends the image to Gemini 1.5 Flash and extracts the required fields.
        
        Args:
            image_bytes: The raw bytes of the image file.
            
        Returns:
            dict: A dictionary containing 'ingredient', 'manufacturer', and 'quantity_g'.
                  Returns None if extraction fails.
        """
        if not self.model:
            return None

        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            prompt = """
            Extract the following fields from the product label: 
            'Ingredient Name', 'Manufacturer Name', 'Quantity in grams'. 
            
            Return ONLY a raw JSON object. Do not use Markdown formatting (no ```json blocks).
            For 'quantity_g', return ONLY the number (e.g. 500, not 500g). If it is in kg, convert to grams.
            Ignore marketing text.
            
            JSON Structure: {"ingredient": str, "manufacturer": str, "quantity_g": str or number}
            """

            response = self.model.generate_content([prompt, image])
            
            # Clean up the response text to ensure it's valid JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text)
            
            # Post-process quantity to ensure it's just a number
            if "quantity_g" in data and data["quantity_g"]:
                # Convert to string, strip 'g', 'kg', spaces
                qty_str = str(data["quantity_g"]).lower()
                # Simple cleaning: keep only digits and dots/commas
                import re
                # Find the first number pattern
                match = re.search(r"[\d\.,]+", qty_str)
                if match:
                    # Normalize comma to dot
                    clean_num = match.group(0).replace(',', '.')
                    data["quantity_g"] = clean_num
                else:
                    data["quantity_g"] = ""
            
            return data

        except Exception as e:
            st.error(f"AI Extraction Error: {e}")
            return None
