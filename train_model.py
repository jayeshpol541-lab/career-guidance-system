import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

# -----------------------------
# Load Dataset
# -----------------------------
data = pd.read_csv("dataset/cleaned_career_guidance_dataset.csv")

# -----------------------------
# Remove Missing Values
# -----------------------------
data.dropna(inplace=True)

# -----------------------------
# Remove ID Column
# -----------------------------
if "Student_ID" in data.columns:
    data.drop("Student_ID", axis=1, inplace=True)

# -----------------------------
# Target Column
# -----------------------------
target_column = "Recommended_Career_Path"

if target_column not in data.columns:
    print("Available Columns:")
    print(data.columns.tolist())
    exit()

# -----------------------------
# Features and Target
# -----------------------------
features_to_use = [
    "Age",
    "Gender",
    "Field_of_Study",
    "Year_of_Study",
    "GPA",
    "Prior_Employment",
    "Career_Interests",
    "Entrepreneurial_Aspirations"
]
X = data[features_to_use]
y = data[target_column]

# -----------------------------
# Convert all text columns to numeric
# -----------------------------
X = pd.get_dummies(X)

# Encode target labels
from sklearn.preprocessing import LabelEncoder

label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)

# -----------------------------
# Train-Test Split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

# -----------------------------
# Train Model
# -----------------------------
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

model.fit(X_train, y_train)

# -----------------------------
# Evaluate
# -----------------------------
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("Accuracy:", round(accuracy * 100, 2), "%")

# -----------------------------
# Save Model
# -----------------------------
os.makedirs("models", exist_ok=True)

joblib.dump(model, "models/career_model.pkl")
joblib.dump(label_encoder, "models/label_encoder.pkl")
joblib.dump(X.columns.tolist(), "models/model_columns.pkl")

print("Model Saved Successfully!")