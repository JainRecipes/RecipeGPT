import json
import requests
import markdown
import os
from dotenv import load_dotenv
import markdown
import re

f = open('static/data/data.json')
recipeData = json.load(f)


repo_owner = "JainRecipes"
repo_name = "JainRecipes.github.io"
folder_path = "_posts"
recipeJson = []

# Load environment variables from .env file
load_dotenv()


access_token = os.getenv("GITHUB_ACCESS_TOKEN")

base_url = "https://api.github.com/repos/{}/{}/contents/{}".format(repo_owner, repo_name, folder_path)



headers = {
    "Authorization": "token " + access_token
}


def fetch_markdown_files():
    response = requests.get(base_url, headers=headers)
    data = response.json()
    #print(data)
    if len(data)-1 != len(recipeData):
        for file in data:
            
            if file["type"] == "file" and file["name"].endswith(".markdown"):
                file_url = file["download_url"]
                fetch_and_process_markdown_file(file_url, file["name"])
        
        writeJson(recipeJson)
    else:
        print("Data is up to date.")

# dealing with one file, write to recipeJson
def fetch_and_process_markdown_file(file_url, filename):
    response = requests.get(file_url)
    markdown_content = response.text
    html_content = markdown.markdown(markdown_content)

    # Process the HTML content as needed
    
    # print(html_content)
    oneRecipe = parseData(html_content, filename)

    writeOneRecipeEntry(oneRecipe)



def parseData(data, filename):
    recipe_dict = {}

    # Extract title, total-time, and amount it makes
    title_match = re.search(r'title:\s+"(.*?)"', data)
    total_time_match = re.search(r'total-time:\s+(.*?)(?=<\/p>)', data)
    makes_match = re.search(r'Makes (\d+)', data)
    serves_match = re.search(r'Serves (\d+-\d+)', data)
    image_match = re.search(r'image:\s+(.*?)(?=\s|$)', data)



    if title_match:
        recipe_dict['title'] = title_match.group(1)
    if total_time_match:
        recipe_dict['total-time'] = total_time_match.group(1)
    if makes_match:
        recipe_dict['makes'] = int(makes_match.group(1))
    if serves_match:
        recipe_dict['serves'] = serves_match.group(1)
    if image_match:
        recipe_dict['image'] = generateImageURL(image_match.group(1))
    
    recipe_dict['link'] = generateRecipeURL(filename)

    # Extract ingredients - some recpies have 2 tables...
    ingredients_match = re.findall(r'<p>\|\s*Ingredients\s*\|\s* Quantity\s*\|\s*(.*?)<\/p>', data, re.DOTALL)
    #print(str(len(ingredients_match)) + "title: " + title_match.group(1))
    
    if ingredients_match:
        recipe_dict['ingredients'] = []  # empty list
        for ingredients_str in ingredients_match:
            # ingredients_str = ingredients_match.group(1)
            ingredients = re.findall(r'\| (.*?)(?:(?<!\()/.*?)?(?:(?<!\\)/.*?)?\s*\|', ingredients_str)

            for ingredient in ingredients:
                cleaned_ingredient = re.sub(r'\s*\([^)]*\)', '', ingredient.strip())
                if cleaned_ingredient.lower() != "ingredients":
                    recipe_dict['ingredients'].append(cleaned_ingredient)
    
    return recipe_dict



def determineNumIngredients(data):
    pattern = r'<h4>Ingredients<\/h4>'
    matches = re.findall(pattern, data)
    return len(matches)

def generateImageURL(imageData):
    url = "https://raw.githubusercontent.com/JainRecipes/JainRecipes.github.io/master/images/{}".format(imageData)
    return url

def generateRecipeURL(filename):
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})-(.*?)\.markdown', filename)
    if match:
        year, month, day, title = match.groups()

        url = f"https://jainrecipes.github.io/{year}/{month}/{day}/{title}/"
    
        return url



def writeOneRecipeEntry(data):
    recipeJson.append(data)


def writeJson(data):
    
    file_path = "static/data/data.json"

    with open(file_path, "w") as json_file:
        json.dump(data, json_file)
    
    print("JSON data with arrays written to", file_path)


fetch_markdown_files()
