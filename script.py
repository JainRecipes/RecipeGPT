import json
import requests
import markdown
import os
from dotenv import load_dotenv
import markdown
import re
from datetime import datetime, timedelta

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
    
    date_line = re.search(r'^date:.*$', data, re.IGNORECASE | re.MULTILINE)

    recipe_dict['date'] = adjust_date_with_offset(date_line.group())
    print(recipe_dict['date'])
    recipe_dict['link'] = generateRecipeURL(recipe_dict['date'], recipe_dict['title'])

    # Extract ingredients - some recpies have 2 tables...
    ingredients_match = re.findall(r'<p>\|\s*Ingredients\s*\|\s* Quantity\s*\|\s*(.*?)<\/p>', data, re.DOTALL)
    #print(str(len(ingredients_match)) + "title: " + title_match.group(1))
    
    if ingredients_match:
        recipe_dict['ingredients'] = []  # empty list
        for ingredients_str in ingredients_match:
            # ingredients_str = ingredients_match.group(1)
            ingredients = re.findall(r'\| (.*?)\s*\|.*\n', ingredients_str)
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

def adjust_date_with_offset(date_str):
    date_parts = date_str.split()
    offset_hours = int(date_parts[-1]) // 100  # Extracting hours from the offset
    offset_minutes = int(date_parts[-1]) % 100  # Extracting minutes from the offset
    offset = timedelta(hours=offset_hours, minutes=offset_minutes)
    
    date_time_str = " ".join(date_parts[1:3])
    date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S") 
    
    if date_parts[-2] != "-":
        adjusted_date = date_time_obj - offset
    else:
        adjusted_date = date_time_obj + offset
    
    return adjusted_date.strftime("%Y-%m-%d %H:%M:%S")



def generateRecipeURL(date, title):
    #match = re.search(r'(\d{4})-(\d{2})-(\d{2})-(.*?)\.markdown', date)
    #print(date)
    match = re.match(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2}:\d{2})', str(date))

    # convert between utc and etc


    if match:
        
        year = match.group(1)
        month = match.group(2)
        day = match.group(3)

        title = title.replace(" ", "-").lower()

        url = f"https://jainrecipes.github.io/{year}/{month}/{day}/{title}/"
    
        return url



def writeOneRecipeEntry(data):
    recipeJson.append(data)


def writeJson(data):
    
    file_path = "static/data/data.json"

    with open(file_path, "w") as json_file:
        json.dump(data, json_file)
    
    print("JSON data with arrays written to", file_path)


