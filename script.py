import json
import requests
import markdown


repo_owner = "your_username"
repo_name = "your_repository"
folder_path = "path_to_folder_within_repository"


def writeOneRecipeEntry():


def gatherData():

    numRecipes = 

    for _ in range(numRecipes)
    
    return data



def writeJson(data):
    
    file_path = "static/data/data.json"

    with open(file_path, "w") as json_file:
        json.dump(data, json_file)
    
    print("JSON data with arrays written to", file_path)


recipeData = gatherData()
writeJson(recipeData)