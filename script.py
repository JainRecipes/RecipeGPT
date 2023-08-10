import json
import requests
import markdown
import os
from dotenv import load_dotenv
import markdown
import re
from datetime import datetime, timedelta

# load the data
f = open('static/data/data.json')
recipeData = json.load(f)

# constants of what to scrape
repo_owner = "JainRecipes"
repo_name = "JainRecipes.github.io"
folder_path = "_posts" # this stores all the markdown files
recipeJson = []

# Load environment variables from .env file
load_dotenv()

access_token = os.getenv("GITHUB_ACCESS_TOKEN")

base_url = "https://api.github.com/repos/{}/{}/contents/{}".format(repo_owner, repo_name, folder_path)


headers = {
    "Authorization": "token " + access_token
}

# fetch all the markdown files & write it into a json
def fetch_markdown_files():
    response = requests.get(base_url, headers=headers)
    data = response.json()
    #print(data)
    # check if new recipes have been added or not... -1 because there is a "dir" in the data
    if len(data)-1 != len(recipeData):
        for file in data:
            # for all the files, take and download only the markdown ones
            if file["type"] == "file" and file["name"].endswith(".markdown"):
                file_url = file["download_url"]
                # process the markdown... get the right content and append to the json
                fetch_and_process_markdown_file(file_url, file["name"])
        
        writeJson(recipeJson)
    else:
        print("Data is up to date.")

# dealing with one file, write to recipeJson
def fetch_and_process_markdown_file(file_url, filename):
    response = requests.get(file_url)
    markdown_content = response.text
    html_content = markdown.markdown(markdown_content)

    # Process the HTML content into the json format we want
    oneRecipe = parseData(html_content, filename)

    writeOneRecipeEntry(oneRecipe)


def writeOneRecipeEntry(data):
    recipeJson.append(data)


def parseData(data, filename):
    recipe_dict = {}

    # Extract title, total-time, amount it makes, etc
    title_match = re.search(r'title:\s+"(.*?)"', data)
    total_time_match = re.search(r'total-time:\s+(.*?)(?=<\/p>)', data)
    makes_match = re.search(r'Makes (\d+)', data)
    serves_match = re.search(r'Serves (\d+-\d+)', data)
    image_match = re.search(r'image:\s+(.*?)(?=\s|$)', data)

    # add it to the dictionary/json entry.. group 1 is important
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
    
    # parse the date -> needed for the title because you need to adjust for est/utc
    date_line = re.search(r'^date:.*$', data, re.IGNORECASE | re.MULTILINE)

    # adjust the timezone
    recipe_dict['date'] = adjust_date_with_offset(date_line.group())
    #print(recipe_dict['date'])
    # generate the url, based on the date with offset and the filename
    recipe_dict['link'] = generateRecipeURL(recipe_dict['date'], filename)

    # Extract ingredients - some recpies have 2 or even 3 tables...
    ingredients_match = re.findall(r'<p>\|\s*Ingredients\s*\|\s* Quantity\s*\|\s*(.*?)<\/p>', data, re.DOTALL)
    #print(str(len(ingredients_match)) + "title: " + title_match.group(1))
    
    if ingredients_match:
        recipe_dict['ingredients'] = []  # empty list
        for ingredients_str in ingredients_match:
            # ingredients_str = ingredients_match.group(1)
            # finds all ingredients, ignoring the quantity side of the table
            ingredients = re.findall(r'\| (.*?)\s*\|.*\n', ingredients_str)
            for ingredient in ingredients:
                # clean it by getting rid of anything in parentheses and whitespace
                cleaned_ingredient = re.sub(r'\s*\([^)]*\)', '', ingredient.strip())
                if cleaned_ingredient.lower() != "ingredients":
                    # get rid of the word ingredients, post-processing
                    recipe_dict['ingredients'].append(cleaned_ingredient)
    
    return recipe_dict


# finds the number of ingredients... not necessary in the final
def determineNumIngredients(data):
    pattern = r'<h4>Ingredients<\/h4>'
    matches = re.findall(pattern, data)
    return len(matches)

# generates the image url by taking in the image data
def generateImageURL(imageData):
    url = "https://raw.githubusercontent.com/JainRecipes/JainRecipes.github.io/master/images/{}".format(imageData)
    return url

# adjusting the time based on the offset - necessary for the actual webpage urls
def adjust_date_with_offset(date_str):
    date_parts = date_str.split()
    offset_hours = int(date_parts[-1]) // 100  # Extracting hours from the offset
    offset_minutes = int(date_parts[-1]) % 100  # Extracting minutes from the offset
    offset = timedelta(hours=offset_hours, minutes=offset_minutes)
    
    date_time_str = " ".join(date_parts[1:3]) # combine it all
    date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S") 
    
    # based on sign of the offset (ex: -0500 vs +0500)
    if date_parts[-2] != "-":
        adjusted_date = date_time_obj - offset
    else:
        adjusted_date = date_time_obj + offset
    
    return adjusted_date.strftime("%Y-%m-%d %H:%M:%S")


# generate the recpie url
def generateRecipeURL(date, file):
    #match = re.search(r'(\d{4})-(\d{2})-(\d{2})-(.*?)\.markdown', date)
    #print(date)
    # extract the filename and the date/time
    fileMatch = re.search(r'(\d{4})-(\d{2})-(\d{2})-(.*?)\.markdown', file)
    dateMatch = re.match(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2}:\d{2})', str(date))

    # convert between utc and etc
    if fileMatch and dateMatch:
        
        year = dateMatch.group(1)
        month = dateMatch.group(2)
        day = dateMatch.group(3)

        # uses filematch
        title = fileMatch.group(4)

        # format url
        url = "https://jainrecipes.github.io/{}/{}/{}/{}/".format(year, month, day, title)
    
        return url

# write to the json
def writeJson(data):
    
    file_path = "static/data/data.json"

    with open(file_path, "w") as json_file:
        json.dump(data, json_file)
    
    print("JSON data with arrays written to", file_path)


