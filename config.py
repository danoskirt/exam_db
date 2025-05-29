import os
from typing import Optional

# --- Database Configuration ---
SQLALCHEMY_DATABASE_URI: str = 'postgresql://postgres:2449@localhost:5432/exam_db'
SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

# --- File Uploads ---
UPLOAD_FOLDER: str = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- AI Models ---
QA_MODEL_NAME: str = "distilbert-base-uncased-distilled-squad"
QG_MODEL_NAME: str = "t5-small"
EXPLANATION_MODEL_NAME: str = "t5-small"

# --- Grading Settings ---
AI_GRADING_SIMILARITY_THRESHOLD: int = 75
SUSPICIOUS_QUICK_SUBMIT_THRESHOLD_PERCENT: int = 10
SUSPICIOUS_SLOW_SUBMIT_THRESHOLD_PERCENT: int = 150

# --- Email Configuration ---
MAIL_SERVER: str = 'smtp.gmail.com'
MAIL_PORT: int = 587
MAIL_USE_TLS: bool = True
MAIL_USERNAME: Optional[str] = 'daniel.olusola@softwaresolutions-net.com'
MAIL_PASSWORD: Optional[str] = 'xdrc cfol jvud fzgr'
MAIL_SENDER: Optional[str] = MAIL_USERNAME
ADMIN_EMAIL_RECEIVER: str = 'admin@softwaresolutions-net.com'

# --- Security ---
SECRET_KEY: str = 'YH2yTFnzE6zHqXHqk2vl-UEp8dtxNwgoKzoaEJrxVfNwZ1Ke5iv2o0JZsGhYMV-U'
