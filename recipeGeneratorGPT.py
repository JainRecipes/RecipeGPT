from transformers import AutoTokenizer, AutoModelForCausalLM
import re
import random
import os
from dotenv import load_dotenv
import requests
import time
from bs4 import BeautifulSoup


# Load tokenizer and model - https://huggingface.co/pratultandon/recipe-nlg-gpt2
# Credit to PratulTandon for training the GPT-2 model on the RecipeNLG dataset
tokenizer = AutoTokenizer.from_pretrained("pratultandon/recipe-nlg-gpt2")
model = AutoModelForCausalLM.from_pretrained("pratultandon/recipe-nlg-gpt2")


# Load environment variables from .env file
load_dotenv()

# this is only for the spoonacular stuff, which in this version is not being used
API_KEY = os.getenv("SPOONACULAR_API_KEY")

# shuffles a given array and ensures that none of them are the same
def shuffle_unique_n_times(arr, n):
    unique_results = set()

    while len(unique_results) < n:
        # creates a copy of the array, shuffles it, abd store as a tuple
        shuffled = arr.copy()
        random.shuffle(shuffled)
        unique_results.add(tuple(shuffled))

    # conver all the tuples back into lists
    shuffled_results_list = []
    for result in unique_results:
        shuffled_list = list(result)
        shuffled_results_list.append(shuffled_list)

    # returns unique shuffled arrays (necessary for the GPT model to give different results)
    return shuffled_results_list

# generate prompt using the markers required for the GPT model
def GeneratePrompt(ingredients):
    prompt = "<RECIPE_START> <INPUT_START> "

    # string concatenation to generate the prompt
    for index, ingredient in enumerate(ingredients):
        if index != len(ingredients)-1:
            prompt = prompt + ingredient + " <NEXT_INPUT> "
        else:
            # on the last ingredient...
            prompt = prompt + ingredient + " <INPUT_END>"

    return prompt


# GPT-2 model text-generated response based on the ingredients provided by the user
def generateGPTResponse(ingredients):
    final_generated_text=[]
    # create 4 unique varieties/combinations of ingredientes
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

        # parse the data and the markers into json
        parsedData = parseMarkers(generated_text[:recipe_end_index])
        final_generated_text.append(parsedData)


    # return an array of json data to be read by the frontend
    return final_generated_text

# parse the result of the gpt generated text into an easy format to work with (json)
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
    '''if title_match:
        recipeID = getIdSpoonacular(title_match.group(1))
        if recipeID != -1:
            image, sourceUrl = getDataSpoonacular(recipeID)

            recipe['image'] = image
            recipe['link'] = sourceUrl'''
    
    # generating image not using api and instead using google
    recipe['link'], recipe['image'] = googleSearch(title_match.group(1))
    
    return recipe

# google search scraping for a link to recipe and a relevant image
# good because spoonacular has api limits
def googleSearch(foodName):
    # query - ex: "pesto pizza recipe"
    query = foodName + " recipe"
    results = 1

    # results wanted per google search is one because we just want one image/recipe url

    url = f"https://www.google.com/search?q={query}&num={results}&tbm=isch"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    #print(soup)

    # Extract the first image URL and the associated webpage link
    image_url = None
    webpage_link = None


    img_tags = soup.find_all('img')
    # gets all images from the results and ignores all the ones with an alt_value of google
    for img_tag in img_tags:
        alt_value = img_tag.get('alt')
        if alt_value.lower() != "google":
            image_url = img_tag.get("src")
        # gets the image/href associated with the image -> recipe website
        link_tag = img_tag.find_parent("a")
        if link_tag:
            webpage_link = link_tag.get("href")
            # Convert the relative URL to an absolute URL if needed
            if webpage_link.startswith("/url?"):
                webpage_link = re.search(r'(?<=url=)([^&]+)', webpage_link).group(1)

                webpage_link = requests.utils.unquote(webpage_link)

    return webpage_link, image_url

# spoonacular api searching a recipe to get an id
def getIdSpoonacular(recipeName):
    params = {
        "query": recipeName,
        "apiKey": API_KEY
    }
    retry_delay = 10
    BASE_URL = "https://api.spoonacular.com/recipes/complexSearch"
    first_recipe_id = -1

    response = requests.get(BASE_URL, params=params)
    #print(response)

    # 200 = good, 429 = ratelimited
    if response.status_code == 200:
        recipes = response.json()
        # get the first result's recipe ID
        if recipes['totalResults'] != 0:
            first_recipe_id = recipes["results"][0]["id"]

    elif response.status_code == 429:
        print("Rate limit exceeded. Retrying in {} seconds...").format(retry_delay)
        time.sleep(retry_delay)

    return first_recipe_id



def getDataSpoonacular(recipeID):
    params = {
        "apiKey": API_KEY
    }
    retry_delay = 10
    
    BASE_URL = "https://api.spoonacular.com/recipes/{}/information".format(recipeID)

    response = requests.get(BASE_URL, params=params)
    
    # get the first image and source URL to display
    if response.status_code == 200:
        recipes = response.json()
        image = recipes['image']
        sourceUrl = recipes['sourceUrl']

    elif response.status_code == 429:
        print("Rate limit exceeded. Retrying in {} seconds...").format(retry_delay)
        time.sleep(retry_delay)


    return image, sourceUrl