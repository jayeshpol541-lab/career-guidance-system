from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import joblib
import pandas as pd
import sqlite3
import hashlib
import os
import re
from werkzeug.utils import secure_filename
import PyPDF2
import docx

app = Flask(__name__)
app.secret_key = 'super_secret_career_guidance_key'

# Load trained model and utility metadata
model = joblib.load("models/career_model.pkl")
label_encoder = joblib.load("models/label_encoder.pkl")
MODEL_COLUMNS = joblib.load("models/model_columns.pkl")

DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                mobile TEXT NOT NULL,
                cgpa REAL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()
    finally:
        conn.close()

# Initialize the SQLite database on startup
init_db()


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return redirect(url_for('login'))
            
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        conn = get_db_connection()
        try:
            user = conn.execute(
                'SELECT * FROM users WHERE email = ? AND password = ?',
                (email, hashed_password)
            ).fetchone()
        finally:
            conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('login'))
            
    return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        cgpa = request.form.get('cgpa')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))
            
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (name, email, mobile, cgpa, password) VALUES (?, ?, ?, ?, ?)',
                (name, email, mobile, float(cgpa) if cgpa else None, hashed_password)
            )
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))
        except Exception as e:
            flash(f"Error during registration: {str(e)}", "danger")
            return redirect(url_for('register'))
        finally:
            conn.close()
            
    return render_template("register.html")


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    finally:
        conn.close()
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    return render_template("dashboard.html", user=user)


@app.route('/resume')
def resume():
    if 'user_id' not in session:
        flash("Please log in to access the resume analyzer.", "warning")
        return redirect(url_for('login'))
    return render_template("resume.html")


@app.route('/courses')
def courses():
    if 'user_id' not in session:
        flash("Please log in to access course recommendations.", "warning")
        return redirect(url_for('login'))
    return render_template("courses.html")


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Please log in to access your profile.", "warning")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    finally:
        conn.close()
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    return render_template("profile.html", user=user)


@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Extract features from form input
        age = int(request.form['age'])
        gender = request.form['gender']
        field_of_study = request.form['field_of_study']
        year_of_study = int(request.form['year_of_study'])
        gpa = float(request.form['gpa'])
        prior_employment = int(request.form['prior_employment'])
        career_interests = request.form['career_interests']
        entrepreneurial_aspirations = request.form['entrepreneurial_aspirations']

        # Create input DataFrame
        input_data = {
            'Age': [age],
            'Gender': [gender],
            'Field_of_Study': [field_of_study],
            'Year_of_Study': [year_of_study],
            'GPA': [gpa],
            'Prior_Employment': [prior_employment],
            'Career_Interests': [career_interests],
            'Entrepreneurial_Aspirations': [entrepreneurial_aspirations]
        }
        df = pd.DataFrame(input_data)

        # One-hot encode the inputs
        df_encoded = pd.get_dummies(df)

        # Align with training columns
        df_aligned = df_encoded.reindex(columns=MODEL_COLUMNS, fill_value=0)

        # Predict and decode prediction
        prediction = model.predict(df_aligned)
        predicted_career = label_encoder.inverse_transform(prediction)[0]

        return render_template(
            "result.html",
            career=predicted_career
        )
    except Exception as e:
        return f"Prediction Error: {str(e)}", 400


# Helper functions for resume text extraction
def extract_text_from_pdf(filepath):
    try:
        text = ""
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + " "
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""


def extract_text_from_docx(filepath):
    try:
        doc = docx.Document(filepath)
        text = ""
        for para in doc.paragraphs:
            if para.text:
                text += para.text + " "
        return text
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return ""


@app.route('/api/analyze_resume', methods=['POST'])
def api_analyze_resume():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Extract text based on file type
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        text = ""
        if ext == 'pdf':
            text = extract_text_from_pdf(filepath)
        elif ext == 'docx':
            text = extract_text_from_docx(filepath)
        else:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': 'Unsupported file format. Please upload PDF or DOCX.'}), 400
            
        # Clean up temporary file
        if os.path.exists(filepath):
            os.remove(filepath)
            
        if not text.strip():
            return jsonify({'error': 'Could not extract text. Ensure the document is not scanned or empty.'}), 400
            
        # Domain keyword list
        KEYWORDS = {
            'Healthcare': [
                'nurse', 'nursing', 'clinical', 'patient', 'healthcare', 'medical', 
                'medicine', 'hospital', 'triage', 'anatomy', 'cpr', 'bls', 'care', 
                'diagnosis', 'treatment', 'health', 'physician', 'doctor', 'surgery',
                'clinic', 'pediatric', 'icu', 'emergency', 'rn', 'bsn'
            ],
            'Engineering / Tech': [
                'python', 'java', 'c++', 'javascript', 'react', 'html', 'css', 'sql', 
                'developer', 'programming', 'software', 'engineering', 'git', 'aws', 
                'machine learning', 'algorithms', 'web', 'database', 'frontend', 'backend',
                'c#', 'node', 'django', 'flask', 'data structures', 'coding', 'cloud'
            ],
            'Finance / Business': [
                'finance', 'accounting', 'excel', 'cost', 'investment', 'budget', 'valuation', 
                'business', 'strategy', 'marketing', 'sales', 'management', 'financial',
                'analyst', 'audit', 'portfolio', 'revenue', 'tax', 'banking', 'corporate'
            ],
            'Design / UI-UX': [
                'design', 'ui', 'ux', 'figma', 'photoshop', 'illustrator', 'typography', 
                'graphics', 'wireframe', 'portfolio', 'sketch', 'creative', 'adobe', 'user experience',
                'user interface', 'interaction', 'prototype'
            ]
        }
        
        text_lower = text.lower()
        scores = {}
        matched_kws = {}
        
        for category, keyword_list in KEYWORDS.items():
            matched = []
            for kw in keyword_list:
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text_lower):
                    matched.append(kw)
            
            # Normalization formula
            score = min(100, int((len(matched) / 10.0) * 100)) if len(matched) > 0 else 0
            if len(matched) > 0 and score < 15:
                score = 15
            scores[category] = score
            matched_kws[category] = matched
            
        primary_category = max(scores, key=scores.get)
        primary_score = scores[primary_category]
        
        if primary_score == 0:
            primary_category = 'Engineering / Tech'
            primary_score = 15
            scores[primary_category] = 15
            
        recommendations = []
        if primary_category == 'Healthcare':
            recommendations = [
                "Highlight clinical rotations, patient census management, and specific care standards.",
                "Detail experience with electronic health records (EHR) systems.",
                "List critical certifications (e.g. BLS, CPR, ACLS) prominently.",
                "Emphasize clinical decision-making, patient advocacy, and team coordination."
            ]
        elif primary_category == 'Engineering / Tech':
            recommendations = [
                "Add links to your GitHub profile and showcase personal project repositories.",
                "Include a dedicated Technical Skills section grouping languages, frameworks, and databases.",
                "Mention key computer science concepts: Data Structures, Algorithms, and System Design.",
                "Quantify achievements in your projects (e.g., 'reduced load times by 20% using redis caching')."
            ]
        elif primary_category == 'Finance / Business':
            recommendations = [
                "Quantify financial/business achievements (e.g., 'managed $20K budget', 'boosted sales by 12%').",
                "Highlight proficiency in financial modeling, advanced Excel (VLOOKUP, Pivot Tables), or Tableau.",
                "Describe leadership, project coordination, and client communication experiences.",
                "List agile or scrum project management experience if applicable."
            ]
        elif primary_category == 'Design / UI-UX':
            recommendations = [
                "Add a direct link to your design portfolio (Figma, Behance, Dribbble) at the top.",
                "Explain your user research methods, personas, and usability testing phases.",
                "Detail experience creating typography rules, wireframes, design systems, and style guides.",
                "Emphasize collaboration with frontend developers and engineers."
            ]
            
        pivot_advice = ""
        if primary_category == 'Healthcare':
            pivot_advice = (
                "Since your background is in Healthcare/Nursing, transitioning to Tech is a great path! "
                "You have excellent triage, prioritization, and process skills. Consider targeting HealthTech "
                "(Clinical Informatics, Health IT) or starting with Python for Data Analytics. "
                "To optimize your resume for Tech roles, we recommend adding technical keywords (like Python, SQL, Git) "
                "and building a software project representing your medical expertise (e.g., Patient Triage Automation)."
            )
            
        return jsonify({
            'success': True,
            'primary_category': primary_category,
            'primary_score': primary_score,
            'all_scores': scores,
            'matched_keywords': matched_kws[primary_category] if primary_category in matched_kws else [],
            'recommendations': recommendations,
            'pivot_advice': pivot_advice
        })


@app.route('/api/chat', methods=['POST'])
def api_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json or {}
    message = data.get('message', '').strip().lower()
    
    if not message:
        return jsonify({'response': "I'm listening! Please type a question or select a topic."})
        
    def contains_any(words):
        return any(word in message for word in words)
        
    if contains_any(['hello', 'hi', 'hey', 'greetings', 'start', 'howdy']):
        response = (
            "Hello! I am your **AI Career Guidance Advisor** 🎓.\n\n"
            "I can help you with:\n"
            "- 🔄 **Career Transitions** (e.g., pivoting from **Nursing/Healthcare to Engineering/Tech**)\n"
            "- 📄 **Resume Enhancements** and optimizing your ATS score\n"
            "- 📚 **Recommended Courses** and learning paths\n"
            "- 🎯 **Career Predictions** and clarifying dashboard metrics\n\n"
            "What would you like to explore? Feel free to ask a question or click one of the quick chips!"
        )
    elif contains_any(['transition', 'pivot', 'switch', 'change career', 'nursing', 'nurse', 'doctor', 'medical', 'clinical', 'healthcare']):
        response = (
            "Transitioning from **Nursing / Healthcare to Engineering & Tech** is a powerful career pivot! 🔄\n\n"
            "As a healthcare professional, you already possess high-value transferable skills:\n"
            "1. **Critical Thinking & Triage:** Prioritizing tasks under high pressure matches troubleshooting and debugging.\n"
            "2. **Process Orientation:** Medical protocols map directly to algorithmic pipelines and software engineering standards.\n"
            "3. **Domain Knowledge:** HealthTech is a booming sector. Companies value builders who understand clinical workflows.\n\n"
            "**Your Pivot Checklist:**\n"
            "- **Start with Python:** It's beginner-friendly and the standard for data science and automation.\n"
            "- **Study Clinical Informatics:** Bridge your nursing expertise with tech by exploring health data systems.\n"
            "- **Build Health-Tech Projects:** Build a personal project like a 'patient triage dashboard' or an 'appointment scheduler' and upload it to GitHub.\n"
            "- **Rewrite your Resume:** Translate your nursing experience. Emphasize compliance, process coordination, and software/system usage. Use our **[Resume Analyzer](/resume)** to match tech keywords!"
        )
    elif contains_any(['resume', 'cv', 'ats', 'upload', 'scan', 'match']):
        response = (
            "To maximize your **ATS Resume Match Score**:\n\n"
            "1. **Avoid Multi-Column Layouts:** Keep formatting clean and vertical. Many ATS parsers misread tabular data.\n"
            "2. **List Key Tech Skills:** Group them clearly under headings (e.g., *Programming Languages: Python, SQL; Developer Tools: Git, VS Code*).\n"
            "3. **Use the STAR Method:** Focus on impact. Write: *'Created a patient logging script which saved 4 hours of weekly data entry'* instead of *'Responsible for logging patient data'*.\n"
            "4. **Analyze Here:** Head over to our **[Resume Analyzer](/resume)**, drag and drop your PDF/DOCX, and see your category-wise breakdown instantly!"
        )
    elif contains_any(['course', 'learn', 'study', 'class', 'certificate', 'certification', 'training', 'udemy', 'coursera', 'youtube']):
        response = (
            "I recommend checking out our **[Courses Page](/courses)**! We have curated program roadmaps for multiple domains:\n\n"
            "- **Tech / Software Engineering:** Python & Django Full Stack Developer pathway.\n"
            "- **Data Science:** Machine Learning Specialization by DeepLearning.AI.\n"
            "- **Healthcare / Informatics:** Healthcare Informatics Essentials (ideal for pivoting healthcare workers).\n"
            "- **UI/UX Design:** UX/UI Design Masterclass in Figma.\n\n"
            "On the **[Courses](/courses)** tab, click **View Course** on any card to open a custom details roadmap, containing duration, estimated effort, and links to top platforms like Coursera, Udemy, and free YouTube courses!"
        )
    elif contains_any(['predict', 'prediction', 'result', 'recommendation', 'forest', 'interest']):
        response = (
            "Our **Career Prediction Model** evaluates 8 primary factors including your **Field of Study**, **GPA**, **Career Interests**, and **Prior Employment**.\n\n"
            "It runs a Random Forest Classifier to identify which career domain matches your educational and behavioral background.\n"
            "- Try it out on the **[Prediction Page](/)**.\n"
            "- If you've already completed it, check your **[Dashboard](/dashboard)** to see your skill charts!"
        )
    else:
        response = (
            "I'm here to guide you! 🎓\n\n"
            "If you have questions about **transitioning careers** (like Nursing to Tech), **improving your resume**, "
            "or finding **recommended courses**, let me know. You can also use the quick chips below for instant guides!"
        )
        
    return jsonify({'response': response})


if __name__ == "__main__":
    app.run(debug=True)