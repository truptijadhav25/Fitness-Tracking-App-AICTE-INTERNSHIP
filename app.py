from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
import random
import pickle
import os
import pandas as pd
from datetime import datetime  # Ensure datetime is imported

app = Flask(__name__)
app.secret_key = "your_secret_key"
bcrypt = Bcrypt(app)

# --- Database Connection ---
# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.fitness_tracker
users_collection = db.users
workouts_collection = db.workouts
progress_collection = db.progress
exercises_collection = db.exercises

# --- Load Calorie Prediction Model ---
model_path = os.path.join(os.getcwd(), "calorie_model.pkl")  # Use absolute path
if os.path.exists(model_path):
    with open(model_path, "rb") as file:
        model = pickle.load(file)
else:
    model = None
    print(f"Error: 'calorie_model.pkl' not found at {model_path}")



# --- Home Page ---
@app.route('/')
def home():
    return render_template('home.html')

# --- Signup Route ---
# --- Signup Route ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        age = request.form.get('age')  # Get age
        gender = request.form.get('gender')  # Get gender
        height = request.form.get('height')  # Get height
        weight = request.form.get('weight')  # Get weight

        if not name or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('signup'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            flash("Email already registered! Please log in.", "danger")
            return redirect(url_for('login'))

        users_collection.insert_one({
            'name': name,
            'email': email,
            'password': hashed_password,
            'age': age,  
            'gender': gender,  
            'height': height,  
            'weight': weight  
        })

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


# --- Login Route ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Both email and password are required!", "danger")
            return redirect(url_for('login'))

        user = users_collection.find_one({'email': email})

        if user and 'password' in user:
            if bcrypt.check_password_hash(user['password'], password):
                session['user_id'] = str(user['_id'])
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid email or password.", "danger")
        else:
            flash("User not found.", "danger")

        return redirect(url_for('login'))

    return render_template('login.html')

# --- Dashboard Route ---
@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('login'))

    user_data = {
        'user_name': user.get('name', 'User'),
        'calories_burned': user.get('calories_burned', 0),
        'active_minutes': user.get('active_minutes', 0),
        'steps_progress': user.get('steps_progress', 0),
        'calories_progress': user.get('calories_progress', 0),
    }

    # Fetch recent workouts
    recent_workouts = list(workouts_collection.find({'user_id': user['_id']}).sort('date', -1).limit(5))
    for workout in recent_workouts:
        workout["_id"] = str(workout["_id"])  # Convert ObjectId to string

    # Fetch progress data
    progress_entries = list(progress_collection.find({'user_id': user['_id']}).sort('date', 1).limit(10))
    progress_dates = [entry.get('date', datetime.utcnow()).strftime('%Y-%m-%d') for entry in progress_entries]
    progress_data = [entry.get('calories_burned', 0) for entry in progress_entries]

    # Motivational Quotes
    quotes = [
        "Push yourself, because no one else is going to do it for you.",
        "Great things never come from comfort zones.",
        "Success is what comes after you stop making excuses.",
        "Wake up. Work out. Look hot. Kick ass. Repeat."
    ]
    motivational_quote = random.choice(quotes)

    return render_template(
        'dashboard.html',
        user=user_data,
        recent_workouts=recent_workouts,
        progress_dates=progress_dates,
        progress_data=progress_data,
        motivational_quote=motivational_quote
    )

# --- Exercises Route ---
@app.route('/exercises')
def exercises():
    if not session.get('user_id'):
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    exercise_list = list(exercises_collection.find())
    return render_template('exercises.html', exercises=exercise_list)

# --- Predict Calories Route ---
# --- Predict Calories Route ---
@app.route('/calories', methods=['GET', 'POST'])
def predict_calories():
    prediction = None  # Default value
    height_feet = None
    height_inches = None
    ideal_weight = None
    weight_to_lose = None
    calories_to_burn = None
    water_intake = None
    recommended_workouts = []

    if request.method == 'POST':
        try:
            # Get form data safely
            age = request.form.get('age', '').strip()
            height = request.form.get('height', '').strip()
            weight = request.form.get('weight', '').strip()
            duration = request.form.get('duration', '').strip()
            heart_rate = request.form.get('heart_rate', '').strip()
            gender = request.form.get('gender', '').strip().lower()

            # Validate inputs
            if not all([age, height, weight, duration, heart_rate, gender]):
                flash("All fields are required!", "danger")
                return redirect(url_for('dashboard'))

            # Convert inputs to correct data types
            age = float(age)
            height = float(height)  # Height is in cm from slider
            weight = float(weight)
            duration = float(duration)
            heart_rate = float(heart_rate)

            # Convert height from cm to feet & inches
            height_inches = round(height * 0.393701)
            height_feet = height_inches // 12
            remaining_inches = height_inches % 12
            height_display = f"{height_feet}'{remaining_inches}\""

            # Convert height to BMI formula: BMI = weight (kg) / (height (m)²)
            height_meters = height / 100
            bmi = round(weight / (height_meters ** 2), 2)

            # Convert gender to numeric (0 = Female, 1 = Male)
            gender_numeric = 1 if gender == 'male' else 0

            # Ensure model is loaded
            if model is None:
                flash("Error: Calorie prediction model not found.", "danger")
                return redirect(url_for('dashboard'))

            # Prepare input for model

            input_features = [[age, gender_numeric, weight, duration, heart_rate]]


            # Predict calories burned
            prediction = model.predict(input_features)[0]

            # Ideal weight calculation (based on BMI 22)
            ideal_weight = round(22 * (height_meters ** 2), 2)

            # Weight to lose calculation
            weight_to_lose = round(weight - ideal_weight, 2) if weight > ideal_weight else 0

            # Calories to burn per day to reach ideal weight (safe weight loss pace)
            calories_to_burn = round(weight_to_lose * 7700 / 30, 2) if weight_to_lose > 0 else 0

            # Recommended water intake (based on weight)
            water_intake = round((weight * 0.033), 2)

            # Recommended workouts (simple logic)
            if prediction > 300:
                recommended_workouts = ["Running", "Cycling", "Swimming"]
            elif prediction > 150:
                recommended_workouts = ["Brisk Walking", "Jump Rope", "Bodyweight Exercises"]
            else:
                recommended_workouts = ["Light Yoga", "Stretching", "Short Walks"]

            return render_template(
                'calories.html',
                prediction=prediction,
                height_display=height_display,
                bmi=bmi,
                ideal_weight=ideal_weight,
                weight_to_lose=weight_to_lose,
                calories_to_burn=calories_to_burn,
                water_intake=water_intake,
                recommended_workouts=recommended_workouts
            )

        except Exception as e:
            flash(f"Error in calorie prediction: {str(e)}", "danger")
            return redirect(url_for('dashboard'))

    return render_template('calories.html', prediction=prediction)

# Fetch User Details from DB
def get_user_from_db(user_id):
    """Fetch user details from MongoDB by user_id."""
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return {
                "name": user.get("name"),
                "email": user.get("email"),
                "height": user.get("height", "Not Set"),
                "weight": user.get("weight", "Not Set"),
                "age": user.get("age", "Not Set"),
                "gender": user.get("gender", "Not Set")
            }
    except Exception as e:
        print(f"Error fetching user from DB: {e}")
    return None

# Profile Route
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    
    user = get_user_from_db(session['user_id'])
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('login'))
    
    # Ensure weight and height are treated as numbers, defaulting to 0 if invalid
    try:
        user['weight'] = float(user['weight'])
    except (ValueError, TypeError):
        user['weight'] = 0.0  # Default value if weight is invalid

    try:
        user['height'] = float(user['height'])
    except (ValueError, TypeError):
        user['height'] = 0.0  # Default value if height is invalid

    return render_template('profile.html', user=user)



# update route
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('login'))

    # Get updated data from the form
    name = request.form.get('name')
    email = request.form.get('email')
    age = request.form.get('age')
    gender = request.form.get('gender')

    height = request.form.get('height')
    weight = request.form.get('weight')

    # Convert height and weight to float if possible, otherwise store as 0.0
    try:
        height = float(height) if height and height.strip() else 0.0
    except ValueError:
        height = 0.0

    try:
        weight = float(weight) if weight and weight.strip() else 0.0
    except ValueError:
        weight = 0.0

    # Update user data
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "name": name,
            "email": email,
            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight
        }}
    )

    flash("Profile updated successfully!", "success")
    return redirect(url_for('profile'))


# --- Logout Route ---
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))  # Redirect to the home page

if __name__ == '__main__':
    app.run(debug=True)

# --- Home Page ---
@app.route('/')
def home():
    return render_template('home.html')