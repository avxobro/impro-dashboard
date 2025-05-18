import os
import json
from typing import Dict, Any
import openai
from dotenv import load_dotenv


class RFQGenerator:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = openai.OpenAI(api_key=api_key)

    def generate_rfq(self, text_content):
        """Generates RFQ from text content using OpenAI"""
        system_prompt = """
                You are an AI procurement assistant. Your task is to extract and organize structured information from procurement documents.

                Carefully read the input text and extract each individual item being procured. For each item, provide the following fields:

                1. "name": A clear, descriptive name of the item.
                2. "quantity": The number of units mentioned. If not mentioned, assume it is 1.
                3. "description": A short, simple explanation of what the item is, with key specifications. Include known specifications using your general knowledge if not explicitly mentioned in the document. If the item is unclear or ambiguous, set the description to "Not sure about the product."

                Guidelines:
                - Be concise and write in simple English.
                - Do not invent product names—use what's given in the document.
                - Avoid adding unnecessary technical terms unless they are part of the input.

                Return the output in the following JSON format:
                {
                    "items": [
                        {
                            "id": "item1",
                            "name": "Descriptive item name",
                            "quantity": number,
                            "description": "Brief, clear description with key specs"
                        },
                        ...
                    ]
                }
                """


        user_prompt = f"Extract procurement items from the following document text:\n\n{text_content}"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating RFQ: {str(e)}"
        

# class RFQExtractor:
#     def __init__(self, api_key: str):
#         """
#         Initialize the RFQExtractor class with the OpenAI API key.
        
#         Args:
#             api_key (str): The OpenAI API key.
#         """
#         self.openai = OpenAI(api_key=api_key)
#         self.model = "gpt-4o"
#         self.system_prompt = """
#         You are an AI procurement specialist. Extract structured information about items from the provided procurement document.
#         Focus on identifying products, quantities, and key specifications.
#         For each item, provide:
#         1. A descriptive name
#         2. Quantity (if mentioned)
#         3. A brief description with key specifications

#         Return the information in the following JSON format:
#         {
#             "items": [
#                 {
#                     "id": "item1",
#                     "name": "Item name",
#                     "quantity": number,
#                     "description": "Brief description with specifications"
#                 }
#             ]
#         }
#         """

#     async def extract(self, document_text: str) -> Dict[str, Any]:
#         """
#         Extract procurement information from the provided text using OpenAI.

#         Args:
#             document_text (str): Text extracted from a document.

#         Returns:
#             Dict[str, Any]: Structured data in the specified format.
#         """
#         user_prompt = f"Extract procurement items from the following document text:\n\n{document_text}"
        
#         try:
#             response = self.openai.chat.completions.create(
#                 model=self.model,
#                 messages=[
#                     {"role": "system", "content": self.system_prompt},
#                     {"role": "user", "content": user_prompt}
#                 ],
#                 response_format={"type": "json_object"},
#                 temperature=0.2
#             )
            
#             # Parse the JSON response
#             result = json.loads(response.choices[0].message.content)
#             return result
        
#         except Exception as e:
#             print(f"Error in OpenAI extraction: {e}")
#             return {"items": []}
