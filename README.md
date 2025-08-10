# ScanSheet-API

ScanSheet-API is a FastAPI-based backend service for processing scanned forms using AI models. It provides an API endpoint that accepts images of forms, processes them using GPT and Mistral AI models, and returns extracted information.

## Features

- Process scanned forms using AI models (GPT-4.1 and Mistral)
- Convert images to PDF format
- Merge multiple images into a single document
- Secure data transmission with AES-GCM encryption
- Authentication via API token

## Requirements

- Python 3.8+
- Dependencies listed in `api/requirements.txt`
- Environment variables for API keys and encryption

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ScanSheet-API.git
   cd ScanSheet-API
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r api\requirements.txt
   ```

4. Create a `.env` file in the `api` directory with the following variables:
   ```
   AUTH_TOKEN=your_auth_token
   SYMMETRIC_KEY=your_symmetric_key
   GPT_API_KEY=your_gpt_api_key
   MISTRAL_API_KEY=your_mistral_api_key
   ```

## Usage

1. Start the API server:
   ```bash
   cd api
   uvicorn app:app --reload
   ```

2. The API will be available at `http://localhost:8000`

3. Send a POST request to `/process-image` with:
   - Authorization header containing your AUTH_TOKEN
   - JSON payload containing base64-encoded images and a title
   - The payload should be encrypted using the SYMMETRIC_KEY

## API Endpoints

### POST /process-image

Processes one or more images and extracts information using AI models.

**Headers:**
- `Authorization`: Your authentication token
- `Content-Type`: application/json

**Request Body:**
```json
{
  "payload": "encrypted_payload"
}
```

The encrypted payload should contain:
```json
{
  "image_bytes": ["base64_encoded_image1", "base64_encoded_image2", ...],
  "title": "form_type"
}
```

**Response:**
```json
{
  "table": "encrypted_response"
}
```

## Special Form Types

- `ficha_cadastro_individual`: When this title is specified, the API processes all images as a single document, merging them together.

## Security

- All data is encrypted using AES-GCM encryption
- API requests require authentication via an authorization header
- Environment variables are used to store sensitive information
