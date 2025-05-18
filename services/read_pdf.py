import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from dotenv import load_dotenv

class AzureAIPDFReader:
    def __init__(self, endpoint: str, key: str, model_id="prebuilt-layout"):
        """
        Initialize the Azure AI PDF Reader with Document Intelligence credentials
        Args:
            endpoint: Azure Document Intelligence endpoint
            key: Azure Document Intelligence key
            model_id: Model ID to use (default: prebuilt-layout)
        """
        self.endpoint = endpoint
        self.key = key
        self.model_id = model_id
        self.client = DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )

    def extract_text(self, pdf_path: str) -> dict:
        """
        Extract structured text from PDF using Azure AI Document Intelligence
        Args:
            pdf_path: Path to PDF file
        Returns:
            Structured document content including pages, paragraphs, and tables
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            with open(pdf_path, "rb") as f:
                poller = self.client.begin_analyze_document(
                    self.model_id,
                    document=f
                )
                result = poller.result()

            return self._structure_result(result)
        
        except Exception as e:
            raise RuntimeError(f"Error processing PDF: {str(e)}")

    def _structure_result(self, result) -> dict:
        """Structure the Azure Document Intelligence result into a organized format"""
        structured_result = {
            "pages": [],
            "tables": [],
            "paragraphs": []
        }

        # Process pages and their text content
        for page_idx, page in enumerate(result.pages):
            page_content = {
                "page_number": page_idx + 1,
                "lines": []
            }

            # Add just the line text content
            for line in page.lines:
                page_content["lines"].append(line.content)

            structured_result["pages"].append(page_content)

        # Process paragraphs text only
        for paragraph in result.paragraphs:
            structured_result["paragraphs"].append({
                "text": paragraph.content,
                "role": paragraph.role if hasattr(paragraph, 'role') and paragraph.role else "body"
            })

        # Process tables text only
        for table_idx, table in enumerate(result.tables):
            table_data = {
                "table_number": table_idx + 1,
                "rows": table.row_count,
                "columns": table.column_count,
                "cells": []
            }

            # Create a 2D grid to represent the table
            grid = [[None for _ in range(table.column_count)] for _ in range(table.row_count)]
            
            # Fill in the grid with cell content
            for cell in table.cells:
                row = cell.row_index
                col = cell.column_index
                grid[row][col] = cell.content
            
            # Add the grid to the table data
            table_data["grid"] = grid
            structured_result["tables"].append(table_data)

        return structured_result

