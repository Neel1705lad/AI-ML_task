from flask import Flask, request
import pandas as pd
from twilio.twiml.messaging_response import MessagingResponse
import spacy

app = Flask(__name__)

# Load the dataset
file_path = '/mnt/data/NutritionalFacts_Fruit_Vegetables_Seafood.csv'
nutritional_data = pd.read_csv(file_path, encoding='ISO-8859-1')

# Load spaCy model
nlp = spacy.load("en_core_web_sm")


def get_nutritional_info(food_name):
    food_info = nutritional_data[nutritional_data['Food and Serving'].str.contains(food_name, case=False, na=False)]

    if food_info.empty:
        return f"Sorry, I couldn't find nutritional information for {food_name}."

    columns_of_interest = [
        'Calories', 'Total Fat', 'Sodium', 'Potassium',
        'Total Carbo-hydrate', 'Protein', 'Vitamin A', 'Vitamin C', 'Calcium', 'ÊÊIronÊÊ'
    ]

    response = f"Nutritional Information for {food_info['Food and Serving'].values[0]}:\n"
    for col in columns_of_interest:
        col_name = col.replace('Ê', '').strip()
        response += f"- {col_name}: {food_info[col].values[0]}\n"

    return response


def is_healthy_for_adults():
    healthy_foods = nutritional_data[nutritional_data['Calories'] < 100]  # Example criteria
    food_list = healthy_foods['Food and Serving'].tolist()
    return "Healthy foods for adults include:\n" + "\n".join(food_list)


def contains_nutrient(food_name, nutrient):
    food_info = nutritional_data[nutritional_data['Food and Serving'].str.contains(food_name, case=False, na=False)]
    if food_info.empty:
        return f"Sorry, I couldn't find information for {food_name}."

    if nutrient in food_info.columns:
        if pd.notna(food_info[nutrient].values[0]):
            return f"Yes, {food_name} contains {nutrient}."
        else:
            return f"No, {food_name} does not contain {nutrient}."
    else:
        return f"Sorry, I couldn't find information about {nutrient} in {food_name}."


def handle_query(query):
    doc = nlp(query)
    food_name = None
    nutrient = None

    for ent in doc.ents:
        if ent.label_ == "FOOD":
            food_name = ent.text
        if ent.label_ == "NUTRIENT":
            nutrient = ent.text

    if "healthy for adults" in query:
        return is_healthy_for_adults()
    elif food_name and "nutrition" in query:
        return get_nutritional_info(food_name)
    elif food_name and nutrient:
        return contains_nutrient(food_name, nutrient)
    else:
        return "Sorry, I didn't understand that. Please ask specific questions about food and nutrition."


@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    response = MessagingResponse()
    msg = response.message()

    answer = handle_query(incoming_msg)
    msg.body(answer)

    return str(response)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
