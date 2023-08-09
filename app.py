import script
import recipeGeneratorGPT
from flask import Flask, render_template, redirect, url_for, request, jsonify
import json
import Levenshtein
from fuzzywuzzy import fuzz


f = open('static/data/data.json')
recipeData = json.load(f)

def numberOfRecipes(data):
    return len(data)
    
# find all ingredients from json data
def findIngredients(data):
    all_ingredients = set()
    for recipe in data:
        ingredients = recipe.get('ingredients')
        if ingredients:
            for ingredient in ingredients:
                lowercase_ingredient = ingredient.lower()
                all_ingredients.add(lowercase_ingredient.capitalize())
        
    ingredients = list(all_ingredients)
    ingredients.sort()
    return ingredients

def group_similar_strings(strings_list, threshold=6):
    groups = []
    for string in strings_list:
        matched = False
        for group in groups:
            for member in group:
                if Levenshtein.distance(string.lower(), member.lower()) <= threshold:
                    group.append(string)
                    matched = True
                    break
        if not matched:
            groups.append([string])
    return groups

def group_similar_strings2(strings_list, threshold=100):
    groups = []
    for string in strings_list:
        matched = False
        for group in groups:
            for member in group:
                if fuzz.partial_ratio(string, member) >= threshold:
                    group.append(string)
                    matched = True
                    break
        if not matched:
            groups.append([string])
    return groups

def determineMatchingRecipes(options):
    filtered_recipes = []

    # Loop through the recipes and check if any checked option exists in the ingredients
    for recipe in recipeData:
        ingredients = recipe.get('ingredients', [])
        if any(option in ingredients for option in options):
            filtered_recipes.append(recipe)
    #print(filtered_recipes)
    return filtered_recipes

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle the POST request and redirect to ingredients.html
        return redirect(url_for('ingredients'))
    else:
        # Render the index.html template for the GET request
        numRecipes = numberOfRecipes(recipeData)


        return render_template('index.html', numRecipes=numRecipes)

@app.route('/ingredients', methods=['GET', 'POST'])
def ingredients():
    # Render the index.html template for the GET request
    ingredientList = findIngredients(recipeData)
    ingredient_groups = group_similar_strings2(ingredientList)

    unique_ingredients = [group[0] for group in ingredient_groups]

    return render_template('ingredients.html', ingredients=unique_ingredients)

@app.route('/results', methods=['POST'])
def results():
    checked_options=request.form.getlist('option')
    #print("Checked options: ", checked_options)

    recipesData=determineMatchingRecipes(checked_options)
    gptSuggestions = recipeGeneratorGPT.generateGPTResponse(checked_options)
    
    return render_template('results.html', options=checked_options, recipes=recipesData, gptSuggestions=gptSuggestions)


@app.route('/tomato', methods=['GET'])
def tomato():
    if request.method == 'GET':
        return render_template('tomato.html')
   


if __name__ == '__main__':
    script.fetch_markdown_files()
    app.run(debug=True)
