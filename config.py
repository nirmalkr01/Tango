import os

class Config:
    # Google API Key
    GOOGLE_API_KEY = "***************"
    # Flask Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Newton@4173'