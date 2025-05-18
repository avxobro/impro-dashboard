from typing import List, Dict
import os
import json
import uuid
import openai
from dotenv import load_dotenv
from models import ItemDetail

class ContentVerifier:
    def __init__(self):
        '''
        Initializes the ContentVerifier class by loading environment variables and setting up the OpenAI client.
        '''
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ Missing OpenAI API Key")
        self.client = openai.OpenAI(api_key=api_key)

    def verify_rfq(self, text_content: str) -> bool:
        '''
        Verifies whether the provided text content is an RFQ.
        Args:
            text_content (str): The content to be verified as an RFQ.
        Returns:
            bool: True if the content is identified as an RFQ, False otherwise.
        '''
        rfq_filter = (
            "You are a helpful assistant. Identify if the following text is a Request for Quotation (RFQ). "
            "Return exactly 'True' or 'False'. Keywords: RFQ, Request for Quotation, Quotation request, Pricing request."
        )

        verification_resp = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": rfq_filter},
                {"role": "user", "content": text_content}
            ],
            temperature=0,
            max_tokens=10
        )

        verification = verification_resp.choices[0].message.content.strip()
        return verification == "True"

    def generate_rfq(self, text_content: str) -> tuple[List[ItemDetail], bool]:
        '''
        Extracts RFQ items from the provided text content and returns verification status.
        Args:
            text_content (str): The text content to extract RFQ items from.
        Returns:
            Tuple[List[ItemDetail], bool]: A list of extracted items and verification status.
        '''
        extraction_rules = (
            "You are a helpful assistant. Extract a list of procurement items from the text "
            "and return JSON exactly in this format:\n"
            "{\n"
            "  \"items\": [\n"
            "    {\n"
            "      \"name\": \"Item name\",\n"
            "      \"quantity\": 1,\n"
            "      \"description\": \"Brief description\"\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Only return JSON without any additional commentary."
        )

        verification_status = self.verify_rfq(text_content)
        if not verification_status:
            return [], False

        rfq_response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": extraction_rules},
                {"role": "user", "content": text_content}
            ],
            temperature=0.5,
            max_tokens=1000
        )

        rfq_json = rfq_response.choices[0].message.content.strip()

        try:
            rfq_data = json.loads(rfq_json)
            items_list = []
            for item in rfq_data.get("items", []):
                if item.get("name", "").startswith("Wrong Request") or not item.get("name"):
                    continue
                item_detail = ItemDetail(
                    id=str(uuid.uuid4()),
                    name=item.get("name", "Unknown Item"),
                    quantity=item.get("quantity", 1),
                    description=item.get("description", "")
                )
                items_list.append(item_detail)
            return (items_list, verification_status)
        except json.JSONDecodeError:
            print("❌ JSON decoding failed.")
        return ([], verification_status)
