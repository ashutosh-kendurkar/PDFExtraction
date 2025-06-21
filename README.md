# PDF Extraction Web App

This project provides a FastAPI backend and a simple HTML UI for uploading a PDF along with metadata. When a PDF is uploaded, the app extracts multiple-choice questions, uploads any images to Firebase Storage, and stores the data in Firestore.

## Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Provide a Firebase service account key as `serviceAccount.json` and update the storage bucket name in `api/upload.py`.
3. Start the server:
   ```bash
   uvicorn api.upload:app --reload
   ```
4. Open `static/index.html` in the browser and submit the form.

The project is ready to deploy on Vercel using the provided `vercel.json` configuration.

