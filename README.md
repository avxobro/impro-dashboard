# PDF Processing with Azure Document Intelligence

This project integrates Azure Document Intelligence for advanced PDF text extraction, providing better results than traditional PDF readers.

## Integration Components

- **AzureAIPDFReader** (`services/read_pdf.py`) - A wrapper class for Azure Document Intelligence API to extract text from PDFs
- **Document Processor** (`services/document_processor.py`) - Now uses AzureAIPDFReader for PDF processing

## Configuration

Azure Document Intelligence credentials are configured in `config.py` and can be set through environment variables:

- `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`: Azure endpoint URL
- `AZURE_DOCUMENT_INTELLIGENCE_KEY`: Azure API key

You can add these to a `.env` file in the project root:

```
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_endpoint_here
AZURE_DOCUMENT_INTELLIGENCE_KEY=your_key_here
```

## PDF Processing Features

The Azure Document Intelligence integration provides:

- Improved text extraction with layout recognition
- Table detection and extraction
- Structured paragraphs with role identification
- Fallback to PyPDF2 when Azure credentials are unavailable or when errors occur

## Output Format

AzureAIPDFReader returns a structured dictionary with:

- **pages**: Array of page objects with text lines
- **paragraphs**: Array of paragraph objects with text content and roles
- **tables**: Array of table objects with row/column data

The document processor converts this structured data into formatted text for use with downstream AI analysis. 