import script
import recipeGeneratorGPT
from flask import Flask, render_template, redirect, url_for, request, jsonify
import json
import Levenshtein
from fuzzywuzzy import fuzz

# load the jainrecipes data
f = open('static/data/data.json')
recipeData = json.load(f)

# simple number of recipes count
def numberOfRecipes(data):
    return len(data)
    
# find all ingredients from json data
def findIngredients(data):
    # creates a set
    all_ingredients = set()
    for recipe in data:
        # gets all the ingredients
        ingredients = recipe.get('ingredients')
        if ingredients:
            for ingredient in ingredients:
                lowercase_ingredient = ingredient.lower()
                all_ingredients.add(lowercase_ingredient.capitalize())

    # gets rid of any exact duplicates    
    ingredients = list(all_ingredients)
    # alphabetizes
    ingredients.sort()
    return ingredients

# similar strings represented by just one (all-purpose flower and all purpose flower)
def group_similar_strings(strings_list, threshold=6):
    groups = []
    for string in strings_list:
        matched = False
        for group in groups:
            for member in group:
                # uses levenshtein distance to see difference between strings
                if Levenshtein.distance(string.lower(), member.lower()) <= threshold:
                    group.append(string)
                    matched = True
                    break
        if not matched:
            groups.append([string])
    return groups

# same thing but uses a different library, fuzzywuzzy's partial_ratio
def group_similar_strings2(strings_list, threshold=95):
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

# find the matching recipes to see if it has any of the relevant ingredients
def determineMatchingRecipes(options):
    filtered_recipes = []

    # Loop through the recipes and check if any checked option exists in the ingredients
    for recipe in recipeData:
        ingredients = recipe.get('ingredients', [])
        if any(option in ingredients for option in options):
            filtered_recipes.append(recipe)
    #print(filtered_recipes)
    return filtered_recipes


# FLASK application
app = Flask(__name__)

# home page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle the POST request and redirect to ingredients.html
        return redirect(url_for('ingredients'))
    else:
        # Render the index.html template for the GET request
        numRecipes = numberOfRecipes(recipeData)


        return render_template('index.html', numRecipes=numRecipes)

# ingredients list page
@app.route('/ingredients', methods=['GET', 'POST'])
def ingredients():
    # Render the index.html template for the GET request
    ingredientList = findIngredients(recipeData)
    ingredient_groups = group_similar_strings2(ingredientList)
    # extracts first element of each group in all the groups
    unique_ingredients = [group[0] for group in ingredient_groups]

    return render_template('ingredients.html', ingredients=unique_ingredients)

# results page
@app.route('/results', methods=['POST'])
def results():
    checked_options=request.form.getlist('option')
    #print("Checked options: ", checked_options)

    recipesData=determineMatchingRecipes(checked_options)
    # determines suggestions from the GPT model - the inference api version is not as good
    gptSuggestions = recipeGeneratorGPT.generateGPTResponse(checked_options)
    
    return render_template('results.html', options=checked_options, recipes=recipesData, gptSuggestions=gptSuggestions)

# fun :)
@app.route('/tomato', methods=['GET'])
def tomato():
    if request.method == 'GET':
        return render_template('tomato.html')
   


if __name__ == '__main__':
    # update the script/check for any changes on jainrecipes
    script.fetch_markdown_files()
    # run the app
    app.run(debug=True)
