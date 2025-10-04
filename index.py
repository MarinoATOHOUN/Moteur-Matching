from main import app
from mangum import Mangum  # adaptateur ASGI -> AWS Lambda-like

handler = Mangum(app)
