from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import ijson

import ingestion

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html>
        <head>
            <title>Product Ingestion Form</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
        </head>
        <body style="padding: 4rem">
            <form action="/upload/" enctype="multipart/form-data" method="post" id="uploadForm">
                <label>
                    Upload product file
                    <input type="file" name="file"/>
                </label>
                <button type="submit">Submit</button>
            </form>
            <div id="message"></div>
            <script>
                document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const form = e.target;
                    const formData = new FormData(form);
                    const messageDiv = document.getElementById('message');
                    messageDiv.innerHTML = `<p>Uploading...</p>`
                    try {
                        const response = await fetch(form.action, {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.json();
                        if (response.ok) {
                            messageDiv.innerHTML = `<p>Successfully uploaded ${result.filename}!</p>`;
                        } else {
                            messageDiv.innerHTML = `<p>Error: ${result.detail || 'Upload failed'}</p>`;
                        }
                    } catch (error) {
                        messageDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
                    }
                });
            </script>
        </body>
    </html>
    """


@app.post("/upload/")
async def ingest_product_json(file: UploadFile = File(...)):
    try:
        async for product in ingestion.products(file):
            print(product.product_name)
        return {"filename": file.filename}
    except Exception as e:
        return {"detail": str(e)}, 400
