from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import fitz
import io
import re
from uuid import uuid4

import firebase_admin
from firebase_admin import credentials, storage, firestore

# Initialize Firebase using a service account key.
# Replace 'serviceAccount.json' and the storage bucket with your own values.
cred = credentials.Certificate('serviceAccount.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': '<your-bucket>.appspot.com'
})

db = firestore.client()
bucket = storage.bucket()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

QUESTION_PATTERN = re.compile(r"(\d+\.\s.*?)(?=\n\d+\.\s|\Z)", re.S)


def extract_questions(pdf_bytes: bytes):
    questions = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            for block in re.findall(QUESTION_PATTERN, text):
                lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
                if not lines:
                    continue
                q = lines[0]
                options = lines[1:]
                questions.append({'question': q, 'options': options})
    return questions


def extract_images(pdf_bytes: bytes):
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    urls = []
    for page_index in range(len(doc)):
        page = doc[page_index]
        for img in page.get_images(full=True):
            xref = img[0]
            base = doc.extract_image(xref)
            image_bytes = base['image']
            ext = base['ext']
            blob_name = f"questions/{uuid4()}.{ext}"
            blob = bucket.blob(blob_name)
            blob.upload_from_string(image_bytes, content_type=f"image/{ext}")
            blob.make_public()
            urls.append(blob.public_url)
    return urls


@app.post('/api/upload')
async def upload(file: UploadFile = File(...),
                 class_: str = Form(...),
                 subject: str = Form(...),
                 lesson: str = Form(...)):
    data = await file.read()
    questions = extract_questions(data)
    image_urls = extract_images(data)

    for q in questions:
        image_url = image_urls.pop(0) if image_urls else None
        doc_ref = db.collection('questions').document()
        doc_ref.set({
            'class': class_,
            'subject': subject,
            'lesson': lesson,
            'question': q['question'],
            'options': q['options'],
            'answer': None,
            'image': image_url
        })
    return JSONResponse({'status': 'success'})

