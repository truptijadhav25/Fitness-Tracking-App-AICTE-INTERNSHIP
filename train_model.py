import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

# Load Data
calories_df = pd.read_csv("../data/calories.csv")
exercise_df = pd.read_csv("../data/exercise.csv")

# Merge datasets on User_ID
data = pd.merge(calories_df, exercise_df, on="User_ID")

# Features & Target
X = data[['Age', 'Height', 'Weight', 'Duration', 'Heart_Rate']]
y = data['Calories']

# Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Model
model = LinearRegression()
model.fit(X_train, y_train)

# Save Model
with open("calorie_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Model trained and saved successfully as 'calorie_model.pkl'")
