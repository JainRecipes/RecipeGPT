from transformers import AutoTokenizer, AutoModelForCausalLM
import re
import random
import os
from dotenv import load_dotenv
import requests
import time


# Load tokenizer and model - https://huggingface.co/pratultandon/recipe-nlg-gpt2
# Credit to PratulTandon for training the GPT-2 model on the RecipeNLG dataset
tokenizer = AutoTokenizer.from_pretrained("pratultandon/recipe-nlg-gpt2")
model = AutoModelForCausalLM.from_pretrained("pratultandon/recipe-nlg-gpt2")


# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("SPOONACULAR_API_KEY")


def shuffle_unique_n_times(arr, n):
    unique_results = set()

    while len(unique_results) < n:
        shuffled = arr.copy()
        random.shuffle(shuffled)
        unique_results.add(tuple(shuffled))

    shuffled_results_list = []
    for result in unique_results:
        shuffled_list = list(result)
        shuffled_results_list.append(shuffled_list)

    return shuffled_results_list

def GeneratePrompt(ingredients):
    prompt = "<RECIPE_START> <INPUT_START> "

    for index, ingredient in enumerate(ingredients):
        if index != len(ingredients)-1:
            prompt = prompt + ingredient + " <NEXT_INPUT> "
        else:
            prompt = prompt + ingredient + " <INPUT_END>"

    return prompt

def generateGPTResponse(ingredients):
    final_generated_text=[]
    ingredientVarieties = shuffle_unique_n_times(ingredients, 4)
    for index, ingredientOrder in enumerate(ingredientVarieties):
        
        prompt = GeneratePrompt(ingredientOrder)

        # Tokenize input and generate text
        input_ids = tokenizer.encode(prompt, return_tensors="pt")
        # max_length is finnicky
        output = model.generate(input_ids, max_length=300, num_return_sequences=1, no_repeat_ngram_size=2, top_k=50, temperature=0.5)

        # Decode generated text
        generated_text = tokenizer.decode(output[0], skip_special_tokens=False)
        recipe_end_index = generated_text.find("<RECIPE_END>")
        print("ORIGINAL DATA")
        print(generated_text)


        # parse the data
        parsedData = parseMarkers(generated_text[:recipe_end_index])
        final_generated_text.append(parsedData)
        print("PARSED DATA")
        print(parsedData)
        print()

    #print()    
    #print(final_generated_text)
    return final_generated_text


def parseMarkers(text):
    recipe = {}

    # Extracting title
    title_match = re.search(r'<TITLE_START>(.*?)<TITLE_END>', text)
    if title_match:
        recipe['title'] = title_match.group(1)

    # Extracting ingredients
    ingr_match = re.search(r'<INGR_START>(.*?)<INGR_END>', text)
    if ingr_match:
        ingredients = [ingr.strip() for ingr in ingr_match.group(1).split('<NEXT_INGR>')]
        recipe['ingredients'] = ingredients

    # Extracting instructions
    instr_match = re.search(r'<INSTR_START>(.*?)<INSTR_END>', text)
    if instr_match:
        instructions = [instr.strip() for instr in instr_match.group(1).split('<NEXT_INSTR>')]
        recipe['instructions'] = instructions
    
    # generating image and a url to instructions using spoonacular api
    if title_match:
        recipeID = getIdSpoonacular(title_match.group(1))
        if recipeID != -1:
            image, sourceUrl = getDataSpoonacular(recipeID)

            recipe['image'] = image
            recipe['link'] = sourceUrl


    return recipe

def getIdSpoonacular(recipeName):
    params = {
        "query": recipeName,
        "apiKey": API_KEY
    }
    retry_delay = 10
    BASE_URL = "https://api.spoonacular.com/recipes/complexSearch"
    first_recipe_id = -1

    response = requests.get(BASE_URL, params=params)
    print(response)


    if response.status_code == 200:
        recipes = response.json()
        print(recipes)
        if recipes['totalResults'] != 0:
            first_recipe_id = recipes["results"][0]["id"]

    elif response.status_code == 429:
        print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)

    return first_recipe_id



def getDataSpoonacular(recipeID):
    params = {
        "apiKey": API_KEY
    }
    retry_delay = 10
    
    BASE_URL = f"https://api.spoonacular.com/recipes/{recipeID}/information"

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        recipes = response.json()
        image = recipes['image']
        sourceUrl = recipes['sourceUrl']

    elif response.status_code == 429:
        print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)


    return image, sourceUrl