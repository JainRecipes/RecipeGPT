from flask import Flask, render_template, redirect, url_for, request
import json
import script


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
    if request.method == 'POST':
        # Handle the POST request and redirect to ingredients.html
        return redirect(url_for('results'))
    else:
        # Render the index.html template for the GET request
        ingredientList = findIngredients(recipeData)
        return render_template('ingredients.html', ingredients=ingredientList)

@app.route('/results', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        # Handle the POST request and redirect to ingredients.html
        return redirect(url_for('results'))
    else:
        # Render the index.html template for the GET request
        return redirect(url_for('index'))

@app.route('/tomato', methods=['GET'])
def tomato():
    if request.method == 'GET':
        return render_template('tomato.html')
   


if __name__ == '__main__':
    app.run(debug=True)
