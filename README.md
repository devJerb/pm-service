# PM Service AI Assistant

A Streamlit-based property management service with AI-powered chat interface using LangChain and Google Gemini.

## Features

- **AI-Powered Chat**: Intelligent conversations using Google Gemini 1.5 Pro
- **Work Categories**: Focus on specific PM tasks (Lease & Contracts, Maintenance & Repairs, Tenant Communications)
- **Adaptive Responses**: AI responses adapt based on selected work category
- **Category-Based File Management**: Organize documents and images by work category with persistent storage
- **Selective File Processing**: Choose which files to include with each message
- **Document Analysis**: Upload and analyze lease agreements, contracts, and maintenance documents
- **Image Processing**: Upload and analyze property photos, damage reports, floor plans, and maintenance images
- **Conversation Memory**: Maintains context throughout your session

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

1. Get your Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### 3. Run the Application

```bash
streamlit run app.py
```

## Usage

1. **Choose Work Category**: Select the type of property management work you're focusing on
2. **Upload Files**: Add documents and images to your selected category (files are saved persistently)
3. **Select Files**: Choose which files to include with your message from the available files in your category
4. **Start a Conversation**: Type your property management questions in the chat
5. **Get Specialized Insights**: The assistant will provide tailored analysis and recommendations based on your selected category and chosen files
6. **Switch Categories**: Change work categories while keeping all your files organized and accessible

## Architecture

```
User Input → Chat Interface → Conversation Manager (with memory) → Gemini LLM → Response
                ↓
         Uploaded Files → Document Processor → Text Extraction → Gemini Analysis
```

## File Structure

- `server/` - LangChain AI service components
  - `config.py` - Gemini LLM configuration
  - `conversation_manager.py` - Conversation handling with memory
  - `document_processor.py` - Document processing and text extraction
  - `image_processor.py` - Image processing and visual analysis preparation
  - `file_manager.py` - Persistent file storage and management
  - `category_manager.py` - Category-based file organization
  - `prompts.py` - Property management specialized prompts
- `components/` - Streamlit UI components
- `data/categories/` - Persistent file storage organized by work category
- `app.py` - Main application entry point

## Supported File Types

- **Documents**: PDF documents (lease agreements, contracts), Word documents (.docx, .doc), Plain text files (.txt)
- **Images**: PNG, JPG, JPEG, GIF, WebP, BMP (property photos, damage reports, floor plans)
- **Data**: Excel files (.xlsx, .xls), CSV files, JSON files

## Troubleshooting

- **API Key Error**: Make sure your `GOOGLE_API_KEY` is correctly set in `.env`
- **Document Processing Error**: Install missing dependencies: `pip install PyPDF2 python-docx`
- **Memory Issues**: The conversation memory resets when you refresh the page (session-based)
