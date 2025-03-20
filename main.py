from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html>
        <head>
            <title>Product Ingestion Form</title>
        </head>
        <body>
            <form>
                <input type="file"/>
            </form>
        </body>
    </html>
    """
