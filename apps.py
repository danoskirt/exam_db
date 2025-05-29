import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from PyPDF2 import PdfReader
import config
import json
from fuzzywuzzy import fuzz
from flask_cors import CORS
import random
import string
import smtplib # For sending emails
from email.mime.text import MIMEText # For formatting email content

# Import configuration
# NOTE: You need to create a 'config.py' file in the same directory
# with variables like SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS,
# UPLOAD_FOLDER, QA_MODEL_NAME, QG_MODEL_NAME, EXPLANATION_MODEL_NAME,
# MAIL_SENDER, MAIL_PASSWORD, MAIL_SERVER, MAIL_PORT, ADMIN_EMAIL_RECEIVER, FUZZY_MATCH_THRESHOLD, DEBUG_MODE


# --- AI Model Imports ---
try:
    from transformers import pipeline, set_seed
    set_seed(42)
except ImportError:
    pipeline = None
    set_seed = None
    print("Warning: 'transformers' library not found. Some AI features will be disabled.")

# Flask App Initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

CORS(app)

db = SQLAlchemy(app)

# --- AI Model Initialization ---
qa_pipeline = None
if pipeline:
    try:
        qa_pipeline = pipeline("question-answering", model=config.QA_MODEL_NAME)
        print(f"Hugging Face QA model '{config.QA_MODEL_NAME}' loaded successfully.")
    except Exception as e:
        print(f"Error loading Hugging Face QA model '{config.QA_MODEL_NAME}': {e}. QA features disabled.")
        qa_pipeline = None

qg_pipeline = None
if pipeline:
    try:
        qg_pipeline = pipeline("text2text-generation", model=config.QG_MODEL_NAME)
        print(f"Hugging Face QG model '{config.QG_MODEL_NAME}' loaded successfully.")
    except Exception as e:
        print(f"Error loading Hugging Face QG model '{config.QG_MODEL_NAME}': {e}. QG features disabled.")
        qg_pipeline = None

explanation_pipeline = None
if pipeline:
    try:
        explanation_pipeline = pipeline("text2text-generation", model=config.EXPLANATION_MODEL_NAME)
        print(f"Hugging Face Explanation model '{config.EXPLANATION_MODEL_NAME}' loaded successfully.")
    except Exception as e:
        print(f"Error loading Hugging Face Explanation model '{config.EXPLANATION_MODEL_NAME}': {e}. Explanation features disabled.")
        explanation_pipeline = None


# --- Database Models (Schema Definition) ---
class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    exam_code = db.Column(db.String(5), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    pass_percentage = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('Question', backref='exam', lazy=True, cascade="all, delete-orphan")
    participants = db.relationship('Participant', backref='exam', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Exam {self.name} ({self.exam_code})>'

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)
    options = db.Column(db.JSON, nullable=True)
    correct_answer = db.Column(db.Text, nullable=True)
    ai_suggested_answer_text = db.Column(db.Text, nullable=True)
    score_points = db.Column(db.Integer, default=1)
    difficulty_score = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<Question {self.id}>'

class ScratchCard(db.Model):
    __tablename__ = 'scratch_cards'
    id = db.Column(db.Integer, primary_key=True)
    pin = db.Column(db.String(20), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_by_participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<ScratchCard {self.pin} (Used: {self.is_used})>'
class Participant(db.Model):
    __tablename__ = 'participants'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    registration_id = db.Column(db.String(6), unique=True, nullable=False)
    __table_args__ = (db.UniqueConstraint('email', 'exam_id', name='_email_exam_uc'),)
    
    scratch_card_pin = db.Column(db.String(20), nullable=False)
    user_pin = db.Column(db.String(4), nullable=False)  # New 4-digit PIN field
    started_at = db.Column(db.DateTime, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Float, nullable=True)
    passed = db.Column(db.Boolean, nullable=True)
    total_questions_answered = db.Column(db.Integer, nullable=True)
    total_correct_answers_count = db.Column(db.Integer, nullable=True)
    is_suspicious = db.Column(db.Boolean, default=False)
    behavioral_data_json = db.Column(db.JSON, nullable=True)
    answers = db.relationship('ParticipantAnswer', backref='participant', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Participant {self.name} ({self.registration_id})>'

class ParticipantAnswer(db.Model):
    __tablename__ = 'participant_answers'
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participants.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    submitted_answer = db.Column(db.Text, nullable=True)
    is_correct = db.Column(db.Boolean, nullable=True)
    score_earned = db.Column(db.Integer, nullable=True)
    time_taken_seconds = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<ParticipantAnswer {self.id}>'

# --- Utility Functions ---

def extract_text_from_pdf(pdf_path):
    """Extracts text content from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def identify_questions_and_answers_ai(text):
    """
    Identifies potential questions and their AI-suggested answers from text.
    Uses Hugging Face QA pipeline if available.
    """
    identified_qas = []
    if qa_pipeline:
        print("Using Hugging Face Transformers for AI extraction...")
        potential_blocks = text.split('\n\n')

        for block in potential_blocks:
            block = block.strip()
            if not block:
                continue

            sentences = [s.strip() for s in block.split('.') if s.strip()]
            question_candidates = []
            context_for_qa = block

            for sentence in sentences:
                if any(kw in sentence.lower() for kw in ['question', 'what', 'who', 'when', 'where', 'why', 'how', 'which', 'is', 'are', 'do', 'does']) and sentence.endswith('?'):
                    question_candidates.append(sentence)
                if any(opt_marker in sentence for opt_marker in ['A)', 'B)', 'C)', 'D)']):
                    context_for_qa = block

            if not question_candidates:
                question_candidates = sentences

            for question_text in question_candidates:
                if not question_text:
                    continue

                try:
                    qa_result = qa_pipeline(question=question_text, context=context_for_qa)
                    ai_answer_text = qa_result['answer'] if qa_result and qa_result['score'] > 0.1 else None
                    score = qa_result['score'] if qa_result else 0.0

                    options = {}
                    import re
                    mcq_pattern = r'([A-D])\)\s*([^A-D\)\(]+)(?:\s*(?=[A-D]\)|\Z))?'
                    mcq_matches = re.findall(mcq_pattern, block)
                    if mcq_matches:
                        for key, value in mcq_matches:
                            options[key.strip()] = value.strip()
                        question_type = 'mcq'
                    else:
                        question_type = 'short_answer'

                    identified_qas.append({
                        'question_text': question_text.replace('\n', ' ').strip(),
                        'ai_suggested_answer_text': ai_answer_text.replace('\n', ' ').strip() if ai_answer_text else None,
                        'confidence_score': round(score, 4),
                        'question_type': question_type,
                        'options': options
                    })
                except Exception as e:
                    print(f"Error running Hugging Face QA pipeline for '{question_text[:50]}...': {e}")
                    identified_qas.append({
                        'question_text': question_text.replace('\n', ' ').strip(),
                        'ai_suggested_answer_text': None,
                        'confidence_score': 0.0,
                        'question_type': 'unknown',
                        'options': {}
                    })
        return identified_qas
    else:
        print("No AI model is configured or loaded for extraction.")
        return []

def generate_unique_pin():
    """Generates a unique alphanumeric PIN for scratch cards (1-20 characters)."""
    characters = string.ascii_letters + string.digits
    pin_length = 12
    while True:
        pin = ''.join(random.choices(characters, k=pin_length))
        if not ScratchCard.query.filter_by(pin=pin).first():
            return pin

def generate_unique_registration_id():
    """Generates a unique 6-character alphanumeric registration ID."""
    characters = string.ascii_uppercase + string.digits
    while True:
        reg_id = ''.join(random.choices(characters, k=6))
        if not Participant.query.filter_by(registration_id=reg_id).first():
            return reg_id

def generate_unique_exam_code():
    """Generates a unique 5-character alphanumeric exam code."""
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(characters, k=5))
        if not Exam.query.filter_by(exam_code=code).first():
            return code

def send_email(subject, body, recipient_email):
    """Sends an email using the configured SMTP settings."""
    sender_email = config.MAIL_SENDER
    sender_password = config.MAIL_PASSWORD
    smtp_server = config.MAIL_SERVER
    smtp_port = config.MAIL_PORT

    if not all([sender_email, sender_password, smtp_server, smtp_port, recipient_email]):
        print("Email configuration or recipient missing. Skipping email send.")
        return False

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")
        return False

# --- API Routes ---

@app.before_request
def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/')
def home():
    return "Exam Backend API is running!"


## Admin Routes


@app.route('/api/admin/generate_scratch_cards', methods=['POST'])
def generate_scratch_cards():
    """
    Admin route to generate a specified number of unique scratch card PINs.
    Scratch cards are now generic and not linked to a specific exam at generation.
    """
    data = request.get_json()
    num_cards = data.get('num_cards', 1)

    if not isinstance(num_cards, int) or num_cards <= 0:
        return jsonify({"error": "Invalid number of cards specified. Must be a positive integer."}), 400

    generated_pins = []
    for _ in range(num_cards):
        pin = generate_unique_pin()
        new_card = ScratchCard(pin=pin) # No exam_id here
        db.session.add(new_card)
        generated_pins.append(pin)
    
    db.session.commit()
    return jsonify({
        "message": f"{num_cards} scratch cards generated successfully.",
        "pins": generated_pins
    }), 201

@app.route('/api/exams', methods=['POST'])
def create_exam():
    """Admin route to create a new exam, generating a 5-digit exam_code."""
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'duration_minutes', 'pass_percentage']):
        return jsonify({"error": "Missing exam details (name, duration_minutes, pass_percentage)"}), 400

    generated_exam_code = generate_unique_exam_code()

    new_exam = Exam(
        exam_code=generated_exam_code,
        name=data['name'],
        duration_minutes=data['duration_minutes'],
        pass_percentage=data['pass_percentage']
    )
    db.session.add(new_exam)
    db.session.commit()

    subject = f"New Exam Created: {new_exam.name}"
    body = (f"A new exam '{new_exam.name}' has been created.\n"
            f"Exam Code: {new_exam.exam_code}\n"
            f"Internal Exam ID: {new_exam.id}\n"
            f"Duration: {new_exam.duration_minutes} minutes\n"
            f"Pass Percentage: {new_exam.pass_percentage}%")
    
    email_sent = send_email(subject, body, config.ADMIN_EMAIL_RECEIVER)
    email_status_message = "Exam code email sent." if email_sent else "Failed to send exam code email."


    return jsonify({
        "message": "Exam created successfully",
        "exam": {
            "id": new_exam.id,
            "exam_code": new_exam.exam_code,
            "name": new_exam.name,
            "duration_minutes": new_exam.duration_minutes,
            "pass_percentage": new_exam.pass_percentage,
            "created_at": new_exam.created_at.isoformat()
        },
        "email_status": email_status_message
    }), 201

@app.route('/api/exams', methods=['GET'])
def get_all_exams():
    exams = Exam.query.all()
    exams_data = []
    for exam in exams:
        exams_data.append({
            "id": exam.id,
            "exam_code": exam.exam_code,
            "name": exam.name,
            "duration_minutes": exam.duration_minutes,
            "pass_percentage": exam.pass_percentage,
            "created_at": exam.created_at.isoformat()
        })
    return jsonify(exams_data), 200

@app.route('/api/exams/<int:exam_id>', methods=['GET'])
def get_exam_by_id(exam_id):
    exam = db.session.get(Exam, exam_id)
    if not exam:
        return jsonify({"error": "Exam not found"}), 404
    return jsonify({
        "id": exam.id,
        "exam_code": exam.exam_code,
        "name": exam.name,
        "duration_minutes": exam.duration_minutes,
        "pass_percentage": exam.pass_percentage,
        "created_at": exam.created_at.isoformat()
    }), 200

@app.route('/api/exams/<int:exam_id>/questions', methods=['POST'])
def add_question_to_exam(exam_id):
    exam = db.session.get(Exam, exam_id)
    if not exam:
        return jsonify({"error": "Exam not found"}), 404

    data = request.get_json()
    if not data or not all(k in data for k in ['question_text', 'question_type']):
        return jsonify({"error": "Missing essential question details (question_text, question_type)"}), 400

    valid_types = ['mcq', 'short_answer', 'true_false']
    if data['question_type'] not in valid_types:
        return jsonify({"error": f"Invalid question_type. Must be one of: {', '.join(valid_types)}"}), 400

    options = data.get('options')
    correct_answer = data.get('correct_answer')
    ai_suggested_answer_text = data.get('ai_suggested_answer_text')

    if data['question_type'] == 'mcq':
        if not isinstance(options, dict) or not options:
            return jsonify({"error": "MCQ questions require 'options' as a non-empty dictionary."}), 400
        if correct_answer and correct_answer not in options:
            return jsonify({"error": "Provided correct_answer for MCQ must be one of the option keys (e.g., 'A', 'B')."}), 400
    else:
        if options:
            return jsonify({"error": "Non-MCQ questions should not have 'options'."}), 400
        if correct_answer is not None and not isinstance(correct_answer, str):
            return jsonify({"error": "Correct answer for non-MCQ must be a string or null."}), 400

    new_question = Question(
        exam_id=exam_id,
        question_text=data['question_text'],
        question_type=data['question_type'],
        options=options,
        correct_answer=correct_answer,
        ai_suggested_answer_text=ai_suggested_answer_text,
        score_points=data.get('score_points', 1),
        difficulty_score=data.get('difficulty_score')
    )
    db.session.add(new_question)
    db.session.commit()
    return jsonify({
        "message": "Question added successfully",
        "question": {
            "id": new_question.id,
            "exam_id": new_question.exam_id,
            "question_text": new_question.question_text,
            "question_type": new_question.question_type,
            "options": new_question.options,
            "correct_answer": new_question.correct_answer,
            "ai_suggested_answer_text": new_question.ai_suggested_answer_text,
            "score_points": new_question.score_points,
            "difficulty_score": new_question.difficulty_score
        }
    }), 201

@app.route('/api/upload_pdf/<int:exam_id>', methods=['POST'])
def upload_pdf_for_questions(exam_id):
    exam = db.session.get(Exam, exam_id)
    if not exam:
        return jsonify({"error": "Exam not found"}), 404

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.lower().endswith('.pdf'):
        filename = f"{exam_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        pdf_text = extract_text_from_pdf(filepath)
        if not pdf_text:
            os.remove(filepath)
            return jsonify({"error": "Failed to extract text from PDF. Is it a searchable PDF?"}), 500

        ai_extracted_qas = identify_questions_and_answers_ai(pdf_text)
        os.remove(filepath)

        return jsonify({
            "message": "PDF processed successfully",
            "extracted_text_preview": pdf_text[:500] + "..." if len(pdf_text) > 500 else pdf_text,
            "ai_suggestions": ai_extracted_qas,
            "exam_id": exam_id,
            "exam_code": exam.exam_code
        }), 200
    else:
        return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400

@app.route('/api/generate_questions', methods=['POST'])
def generate_questions_from_text():
    data = request.get_json()
    text = data.get('text')
    num_questions = data.get('num_questions', 3)

    if not text:
        return jsonify({"error": "No text provided for question generation."}), 400

    generated_qas = []
    if qg_pipeline:
        try:
            input_text = f"generate questions: {text}"
            results = qg_pipeline(input_text, max_length=100, num_beams=5, early_stopping=True, num_return_sequences=num_questions)
            
            for res in results:
                gen_q = res['generated_text'].strip()
                question_type = 'short_answer'
                ai_suggested_answer_text = None

                generated_qas.append({
                    'question_text': gen_q,
                    'question_type': question_type,
                    'options': {},
                    'ai_suggested_answer_text': ai_suggested_answer_text
                })
            return jsonify({"message": "Questions generated successfully (Hugging Face)", "generated_questions": generated_qas}), 200
        except Exception as e:
            print(f"Error generating questions with Hugging Face QG: {e}")
            return jsonify({"error": f"Failed to generate questions using Hugging Face model: {e}"}), 500
    else:
        return jsonify({"error": "No AI model configured for question generation. Please check server logs."}), 500

@app.route('/api/questions/<int:question_id>/explain', methods=['POST'])
def explain_answer(question_id):
    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"error": "Question not found."}), 404
    
    if not question.correct_answer and not question.ai_suggested_answer_text:
        return jsonify({"error": "No correct answer available to explain for this question."}), 400
    
    correct_answer = question.correct_answer or question.ai_suggested_answer_text

    explanation = "No explanation available. AI model not loaded or configured."

    if explanation_pipeline:
        try:
            input_text = f"Explain why '{correct_answer}' is the answer to the question: '{question.question_text}'"
            if question.options:
                input_text += f" Options were: {json.dumps(question.options)}"

            result = explanation_pipeline(input_text, max_length=150, num_beams=5, early_stopping=True)
            explanation = result[0]['generated_text'].strip()
            return jsonify({"message": "Explanation generated (Hugging Face)", "explanation": explanation}), 200
        except Exception as e:
            print(f"Error generating explanation with Hugging Face: {e}")
            return jsonify({"error": f"Failed to generate explanation using Hugging Face model: {e}"}), 500
    else:
        return jsonify({"error": explanation}), 500

@app.route('/api/admin/exams/<int:exam_id>/analyze_difficulty', methods=['GET'])
def analyze_exam_difficulty(exam_id):
    exam = db.session.get(Exam, exam_id)
    if not exam:
        return jsonify({"error": "Exam not found"}), 404

    submitted_participants = Participant.query.filter_by(exam_id=exam_id, submitted_at=True).all()
    if not submitted_participants:
        return jsonify({"message": "No submitted participants for this exam to analyze difficulty."}), 200

    question_performance = {}

    for participant in submitted_participants:
        for answer in participant.answers:
            q_id = answer.question_id
            if q_id not in question_performance:
                question_performance[q_id] = {'correct_count': 0, 'total_attempts': 0}
            
            question_performance[q_id]['total_attempts'] += 1
            if answer.is_correct:
                question_performance[q_id]['correct_count'] += 1
    
    updated_difficulties = []
    for question in exam.questions:
        perf = question_performance.get(question.id)
        if perf and perf['total_attempts'] > 0:
            pass_rate = perf['correct_count'] / perf['total_attempts']
            difficulty = 1.0 - pass_rate
            question.difficulty_score = round(difficulty, 4)
            db.session.add(question)
            updated_difficulties.append({
                "question_id": question.id,
                "question_text": question.question_text[:50] + "...",
                "difficulty_score": question.difficulty_score,
                "pass_rate": round(pass_rate, 4)
            })
    db.session.commit()
    
    return jsonify({
        "message": "Question difficulties updated based on participant performance.",
        "exam_id": exam_id,
        "exam_code": exam.exam_code,
        "difficulty_analysis": updated_difficulties,
        "note": "For a full ML implementation, you would train a regression/classification model on historical data features (question text, type, length, previous performance etc.) to predict difficulty."
    }), 200


## Student Routes

@app.route('/api/register_for_exam', methods=['POST'])
def register_for_exam():
    """
    Allows a student to register for an exam using their details and a scratch card PIN.
    Requires them to create a 4-digit PIN during registration.
    """
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'email', 'scratch_card_pin', 'user_pin']):
        return jsonify({"error": "Missing registration details (name, email, scratch_card_pin, user_pin)"}), 400

    student_name = data['name']
    student_email = data['email']
    scratch_card_pin = str(data['scratch_card_pin'])
    user_pin = str(data['user_pin'])

    # Validate 4-digit PIN
    if not (len(user_pin) == 4 and user_pin.isdigit()):
        return jsonify({"error": "User PIN must be exactly 4 digits."}), 400

    # 1. Validate scratch card pin format
    if not (1 <= len(scratch_card_pin) <= 20) or not scratch_card_pin.isalnum():
        return jsonify({"error": "Scratch card PIN must be 1 to 20 alphanumeric characters."}), 400

    # 2. Find the single existing exam (assumption: there's only one exam)
    exam = Exam.query.first()
    if not exam:
        return jsonify({"error": "No exam found in the system. Please create an exam first (Admin)."}), 404

    # 3. Check if scratch card exists and is unused
    scratch_card = ScratchCard.query.filter_by(pin=scratch_card_pin).first()
    if not scratch_card:
        return jsonify({"error": "Invalid scratch card PIN."}), 400
    if scratch_card.is_used:
        return jsonify({"error": "This scratch card PIN has already been used."}), 400

    # 4. Check if email is already registered for *this specific exam*
    existing_participant = Participant.query.filter_by(email=student_email, exam_id=exam.id).first()
    if existing_participant:
        return jsonify({
            "message": "You are already registered for this exam.",
            "participant_id": existing_participant.id,
            "registration_id": existing_participant.registration_id,
            "exam_id": existing_participant.exam_id,
            "exam_code": exam.exam_code,
            "exam_name": existing_participant.exam.name
        }), 200

    # 5. Generate a unique 6-digit registration ID for the participant
    generated_reg_id = generate_unique_registration_id()

    # 6. Create new participant
    new_participant = Participant(
        exam_id=exam.id,
        name=student_name,
        email=student_email,
        registration_id=generated_reg_id,
        scratch_card_pin=scratch_card_pin,
        user_pin=user_pin,  # Store the 4-digit PIN
        is_suspicious=False,
        behavioral_data_json={}
    )
    db.session.add(new_participant)
    
    # 7. Mark scratch card as used and link to participant
    scratch_card.is_used = True
    scratch_card.used_by_participant_id = new_participant.id
    scratch_card.used_at = datetime.utcnow()
    db.session.add(scratch_card)

    db.session.commit()

    return jsonify({
        "message": "Successfully registered for the exam!",
        "participant_id": new_participant.id,
        "registration_id": new_participant.registration_id,
        "exam_id": exam.id,
        "exam_code": exam.exam_code,
        "exam_name": exam.name,
        "participant_name": new_participant.name,
        "participant_email": new_participant.email,
        "user_pin_set": True  # Confirm PIN was set
    }), 201

@app.route('/api/participants/<int:participant_id>/exam_details', methods=['GET'])
def get_participant_exam_details(participant_id):
    """Get exam ID and other details for a registered participant."""
    participant = db.session.get(Participant, participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    exam = participant.exam
    return jsonify({
        "message": "Exam details retrieved",
        "participant_id": participant.id,
        "exam_id": exam.id,
        "exam_code": exam.exam_code,
        "exam_name": exam.name,
        "registration_id": participant.registration_id
    }), 200

@app.route('/api/student_login', methods=['POST'])
def student_login():
    """
    Allows a registered student to log in using their exam ID and 4-digit PIN.
    """
    data = request.get_json()
    if not data or not all(k in data for k in ['exam_id', 'user_pin']):
        return jsonify({"error": "Missing login credentials (exam_id and user_pin)"}), 400

    exam_id = data['exam_id']
    user_pin = str(data['user_pin'])

    # Validate PIN format
    if not (len(user_pin) == 4 and user_pin.isdigit()):
        return jsonify({"error": "User PIN must be exactly 4 digits."}), 400

    # Find participant by exam ID and PIN
    participant = Participant.query.filter_by(exam_id=exam_id, user_pin=user_pin).first()
    if not participant:
        return jsonify({"error": "Invalid exam ID or PIN. Please check your credentials."}), 401

    exam = participant.exam

    return jsonify({
        "message": "Login successful!",
        "participant_id": participant.id,
        "registration_id": participant.registration_id,
        "exam_id": exam.id,
        "exam_code": exam.exam_code,
        "exam_name": exam.name,
        "duration_minutes": exam.duration_minutes,
        "pass_percentage": exam.pass_percentage,
        "started_at": participant.started_at.isoformat() if participant.started_at else None,
        "submitted_at": participant.submitted_at.isoformat() if participant.submitted_at else None
    }), 200



@app.route('/api/participants/<int:participant_id>/start_exam_session', methods=['POST'])
def start_exam_session(participant_id):
    """
    Allows a participant to start their exam session.
    No longer requires scratch_card_pin in the request body.
    """
    participant = db.session.get(Participant, participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404
    
    if participant.submitted_at:
        return jsonify({"error": "Exam already submitted for this participant."}), 400
    
    if not participant.started_at:
        participant.started_at = datetime.utcnow()
        db.session.commit()
        message = "Exam session started successfully."
        status_code = 200
    else:
        message = "Exam session already in progress (resumed)."
        status_code = 200

    exam = participant.exam
    return jsonify({
        "message": message,
        "participant_id": participant.id,
        "registration_id": participant.registration_id,
        "exam_id": exam.id,
        "exam_code": exam.exam_code,
        "exam_name": exam.name,
        "duration_minutes": exam.duration_minutes,
        "started_at": participant.started_at.isoformat()
    }), status_code


@app.route('/api/participants/<int:participant_id>/questions', methods=['GET'])
def get_exam_questions_for_participant(participant_id):
    """
    Retrieves exam questions for a participant.
    Ensures that sensitive information (correct answers) is not sent to the client.
    """
    participant = db.session.get(Participant, participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    if not participant.started_at:
        return jsonify({"error": "Exam session not started for this participant. Please use /api/participants/<id>/start_exam_session first."}), 400
    if participant.submitted_at:
        return jsonify({"error": "Exam already submitted for this participant. Cannot retrieve questions."}), 400

    exam = participant.exam
    questions_for_client = []
    for q in exam.questions:
        q_data = {
            "id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "options": q.options,
            "score_points": q.score_points
        }
        questions_for_client.append(q_data)

    return jsonify({
        "message": "Questions retrieved successfully.",
        "exam_id": exam.id,
        "exam_code": exam.exam_code,
        "exam_name": exam.name,
        "questions": questions_for_client
    }), 200

@app.route('/api/participants/<int:participant_id>/submit_answer', methods=['POST'])
def submit_answer(participant_id):
    """
    Allows a participant to submit an answer for a specific question.
    Records the answer and checks for correctness upon exam submission.
    """
    participant = db.session.get(Participant, participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    if not participant.started_at:
        return jsonify({"error": "Exam session not started for this participant."}), 400
    if participant.submitted_at:
        return jsonify({"error": "Exam already submitted for this participant. Cannot submit answers."}), 400

    data = request.get_json()
    if not data or not all(k in data for k in ['question_id', 'submitted_answer', 'time_taken_seconds']):
        return jsonify({"error": "Missing answer details (question_id, submitted_answer, time_taken_seconds)"}), 400

    question_id = data['question_id']
    submitted_answer_text = str(data['submitted_answer']).strip()
    time_taken = data['time_taken_seconds']

    question = db.session.get(Question, question_id)
    if not question or question.exam_id != participant.exam_id:
        return jsonify({"error": "Question not found or does not belong to this participant's exam."}), 404

    # Check if the participant has already answered this question
    existing_answer = ParticipantAnswer.query.filter_by(
        participant_id=participant_id,
        question_id=question_id
    ).first()

    if existing_answer:
        # Allow updating an answer if the exam is not yet submitted
        existing_answer.submitted_answer = submitted_answer_text
        existing_answer.time_taken_seconds = time_taken
        db.session.add(existing_answer)
        message = "Answer updated successfully."
    else:
        new_answer = ParticipantAnswer(
            participant_id=participant_id,
            question_id=question_id,
            submitted_answer=submitted_answer_text,
            time_taken_seconds=time_taken
        )
        db.session.add(new_answer)
        message = "Answer submitted successfully."

    db.session.commit() # Commit here to ensure answer is saved before evaluation

    return jsonify({
        "message": message,
        "participant_id": participant_id,
        "question_id": question_id,
        "submitted_answer": submitted_answer_text,
        "time_taken_seconds": time_taken
    }), 200


@app.route('/api/participants/<int:participant_id>/submit_exam', methods=['POST'])
def submit_exam(participant_id):
    """
    Allows a participant to submit their exam.
    Calculates the score, determines pass/fail, and marks the exam as submitted.
    """
    participant = db.session.get(Participant, participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    if not participant.started_at:
        return jsonify({"error": "Exam session not started for this participant."}), 400
    if participant.submitted_at:
        return jsonify({"error": "Exam already submitted for this participant."}), 400

    participant.submitted_at = datetime.utcnow()

    total_score = 0
    total_questions_answered = 0
    total_correct_answers_count = 0
    exam_questions = {q.id: q for q in participant.exam.questions}

    for p_answer in participant.answers:
        question = exam_questions.get(p_answer.question_id)
        if not question:
            continue # Should not happen if data integrity is maintained

        total_questions_answered += 1
        is_correct = False
        score_earned = 0

        # Evaluate answer based on question type
        if question.question_type == 'mcq':
            if question.correct_answer and p_answer.submitted_answer == question.correct_answer:
                is_correct = True
        elif question.question_type == 'short_answer':
            # Use fuzzy matching for short answers
            # FUZZY_MATCH_THRESHOLD should be defined in config.py (e.g., config.FUZZY_MATCH_THRESHOLD = 80)
            if question.correct_answer:
                similarity_ratio = fuzz.ratio(p_answer.submitted_answer.lower(), question.correct_answer.lower())
                if similarity_ratio >= config.FUZZY_MATCH_THRESHOLD: 
                    is_correct = True
            elif question.ai_suggested_answer_text:
                # If no human-defined correct answer, use AI suggested answer for comparison
                similarity_ratio = fuzz.ratio(p_answer.submitted_answer.lower(), question.ai_suggested_answer_text.lower())
                if similarity_ratio >= config.FUZZY_MATCH_THRESHOLD:
                    is_correct = True
        elif question.question_type == 'true_false':
            if question.correct_answer and p_answer.submitted_answer.lower() == question.correct_answer.lower():
                is_correct = True
        
        p_answer.is_correct = is_correct
        if is_correct:
            score_earned = question.score_points
            total_correct_answers_count += 1
        p_answer.score_earned = score_earned
        total_score += score_earned
        db.session.add(p_answer)

    participant.score = total_score
    participant.total_questions_answered = total_questions_answered
    participant.total_correct_answers_count = total_correct_answers_count
    
    # Determine pass/fail
    exam_total_possible_score = sum(q.score_points for q in participant.exam.questions)
    if exam_total_possible_score > 0:
        actual_percentage = (total_score / exam_total_possible_score) * 100
        participant.passed = actual_percentage >= participant.exam.pass_percentage
    else:
        participant.passed = False # No questions, so cannot pass

    db.session.add(participant)
    db.session.commit()

    # Send email notification to participant
    subject = f"Exam Results for {participant.exam.name}"
    body = (f"Dear {participant.name},\n\n"
            f"Your exam '{participant.exam.name}' has been submitted and graded.\n"
            f"Your Registration ID: {participant.registration_id}\n"
            f"Your Score: {participant.score} out of {exam_total_possible_score}\n"
            f"Correct Answers: {participant.total_correct_answers_count} / {total_questions_answered}\n"
            f"Result: {'PASSED' if participant.passed else 'FAILED'}\n\n"
            f"Thank you for participating!")
    send_email(subject, body, participant.email)

    return jsonify({
        "message": "Exam submitted successfully!",
        "participant_id": participant.id,
        "exam_id": participant.exam_id,
        "exam_code": participant.exam.exam_code,
        "score": participant.score,
        "passed": participant.passed,
        "submitted_at": participant.submitted_at.isoformat()
    }), 200

@app.route('/api/participants/<int:participant_id>/results', methods=['GET'])
def get_exam_results(participant_id):
    """
    Retrieves the results for a specific participant.
    """
    participant = db.session.get(Participant, participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    if not participant.submitted_at:
        return jsonify({"error": "Exam not yet submitted for this participant."}), 400

    exam_total_possible_score = sum(q.score_points for q in participant.exam.questions)

    answers_summary = []
    for p_answer in participant.answers:
        question = db.session.get(Question, p_answer.question_id)
        answers_summary.append({
            "question_id": question.id,
            "question_text": question.question_text,
            "submitted_answer": p_answer.submitted_answer,
            "is_correct": p_answer.is_correct,
            "score_earned": p_answer.score_earned,
            "correct_answer_reference": question.correct_answer or question.ai_suggested_answer_text, # For review
            "time_taken_seconds": p_answer.time_taken_seconds
        })

    return jsonify({
        "message": "Exam results retrieved.",
        "participant_id": participant.id,
        "registration_id": participant.registration_id,
        "exam_id": participant.exam.id,
        "exam_code": participant.exam.exam_code,
        "exam_name": participant.exam.name,
        "score": participant.score,
        "total_possible_score": exam_total_possible_score,
        "pass_percentage_required": participant.exam.pass_percentage,
        "passed": participant.passed,
        "total_questions_answered": participant.total_questions_answered,
        "total_correct_answers_count": participant.total_correct_answers_count,
        "submitted_at": participant.submitted_at.isoformat(),
        "is_suspicious": participant.is_suspicious,
        "behavioral_data_json": participant.behavioral_data_json,
        "answers_summary": answers_summary
    }), 200

@app.route('/api/participants/<int:participant_id>/behavioral_data', methods=['PUT'])
def update_behavioral_data(participant_id):
    """
    Allows a participant to submit behavioral data (e.g., focus changes, copy-paste events).
    This data can be used for proctoring/suspicion flagging.
    """
    participant = db.session.get(Participant, participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    data = request.get_json()
    if not data or 'behavioral_event' not in data:
        return jsonify({"error": "Missing behavioral_event data."}), 400

    # Append new behavioral data to the existing JSON array
    current_behavioral_data = participant.behavioral_data_json or []
    current_behavioral_data.append({
        "timestamp": datetime.utcnow().isoformat(),
        "event": data['behavioral_event']
    })
    participant.behavioral_data_json = current_behavioral_data

    # Simple example of flagging suspicion based on a specific event
    if data['behavioral_event'].get('type') in ['focus_lost', 'copy_paste']:
        participant.is_suspicious = True

    db.session.add(participant)
    db.session.commit()

    return jsonify({
        "message": "Behavioral data updated.",
        "participant_id": participant.id,
        "is_suspicious": participant.is_suspicious,
        "latest_event": data['behavioral_event']
    }), 200

## Admin/Reporting Routes


@app.route('/api/participants/<int:participant_id>', methods=['GET'])
def get_participant_details(participant_id):
    """Admin route to get full details of a specific participant."""
    participant = db.session.get(Participant, participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    exam_total_possible_score = sum(q.score_points for q in participant.exam.questions)

    return jsonify({
        "id": participant.id,
        "exam_id": participant.exam_id,
        "exam_name": participant.exam.name,
        "name": participant.name,
        "email": participant.email,
        "registration_id": participant.registration_id,
        "scratch_card_pin": participant.scratch_card_pin,
        "started_at": participant.started_at.isoformat() if participant.started_at else None,
        "submitted_at": participant.submitted_at.isoformat() if participant.submitted_at else None,
        "score": participant.score,
        "total_possible_score": exam_total_possible_score,
        "passed": participant.passed,
        "total_questions_answered": participant.total_questions_answered,
        "total_correct_answers_count": participant.total_correct_answers_count,
        "is_suspicious": participant.is_suspicious,
        "behavioral_data_json": participant.behavioral_data_json,
        "created_at": participant.exam.created_at.isoformat() # Assuming exam creation time is relevant
    }), 200

@app.route('/api/admin/participants', methods=['GET'])
def get_all_participants():
    """Admin route to get a list of all participants with their basic info."""
    participants = Participant.query.all()
    participants_data = []
    for p in participants:
        participants_data.append({
            "id": p.id,
            "name": p.name,
            "email": p.email,
            "registration_id": p.registration_id,
            "exam_name": p.exam.name,
            "exam_code": p.exam.exam_code,
            "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
            "score": p.score,
            "passed": p.passed,
            "is_suspicious": p.is_suspicious
        })
    return jsonify(participants_data), 200

@app.route('/api/admin/participants/<int:participant_id>/answers', methods=['GET'])
def get_participant_answers(participant_id):
    """Admin route to get all answers submitted by a specific participant."""
    participant = db.session.get(Participant, participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    answers_data = []
    for p_answer in participant.answers:
        question = db.session.get(Question, p_answer.question_id)
        answers_data.append({
            "question_id": question.id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "options": question.options,
            "correct_answer": question.correct_answer, # Admin can see correct answer
            "ai_suggested_answer_text": question.ai_suggested_answer_text, # Admin can see AI suggestion
            "submitted_answer": p_answer.submitted_answer,
            "is_correct": p_answer.is_correct,
            "score_earned": p_answer.score_earned,
            "time_taken_seconds": p_answer.time_taken_seconds
        })
    return jsonify({
        "participant_id": participant.id,
        "participant_name": participant.name,
        "exam_name": participant.exam.name,
        "answers": answers_data
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000)
    
