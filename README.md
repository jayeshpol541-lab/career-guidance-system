# Career Guidance System

## Project Overview

The Career Guidance System is a web-based application developed using Python and Flask that helps students identify suitable career paths based on their academic details, interests, and skills. The system uses a Machine Learning model to predict career recommendations and also provides additional resources such as resume analysis and career-related information.

---

## Features

- User Registration and Login
- Career Prediction using Machine Learning
- Resume Upload and Analysis
- Personalized Career Recommendations
- Course Suggestions
- User Profile Management
- Secure Password Storage
- Responsive Web Interface

---

## Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap

### Backend
- Python
- Flask

### Machine Learning
- Scikit-learn
- Pandas
- NumPy
- Joblib

### Database
- SQLite

---

## Project Structure

```
Career-Guidance-System/
│
├── app.py
├── requirements.txt
├── README.md
│
├── dataset/
│   └── career_dataset.csv
│
├── models/
│   └── career_model.pkl
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── resume.html
│   └── result.html
│
├── database/
│   └── users.db
│
└── utils/
    ├── prediction.py
    ├── resume_analyzer.py
    └── preprocessing.py
```

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/Career-Guidance-System.git
```

### Navigate to Project

```bash
cd Career-Guidance-System
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run the Project

```bash
python app.py
```

Open your browser and visit:

```
http://127.0.0.1:5000/
```

---

## Machine Learning Workflow

1. Collect career dataset
2. Clean and preprocess data
3. Encode categorical features
4. Train Random Forest Classifier
5. Save trained model using Joblib
6. Load model in Flask
7. Predict suitable career paths
8. Display recommendations to users

---

## Future Enhancements

- Deep Learning based Career Prediction
- AI Chatbot for Career Counselling
- Barcode/QR Based Student Login
- Resume Score Prediction
- Interview Preparation Module
- College Recommendation System
- Job Recommendation System
- Personality Assessment
- Career Roadmap Generator
- Multi-language Support

---

## Project Screenshots

Add screenshots of:

- Home Page
- Login Page
- Dashboard
- Career Prediction
- Resume Analyzer
- Result Page

---

## Requirements

- Python 3.10+
- Flask
- Pandas
- NumPy
- Scikit-learn
- Joblib
- SQLite

---

## Author

**Jayesh Pol**

B.Tech Computer Science & Engineering (Data Science)

---

## License

This project is developed for educational and learning purposes.
