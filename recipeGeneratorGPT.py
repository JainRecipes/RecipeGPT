from transformers import AutoTokenizer, AutoModelForCausalLM
import re

# Load tokenizer and model - https://huggingface.co/pratultandon/recipe-nlg-gpt2
# Credit to PratulTandon for training the GPT-2 model on the RecipeNLG dataset
tokenizer = AutoTokenizer.from_pretrained("pratultandon/recipe-nlg-gpt2")
model = AutoModelForCausalLM.from_pretrained("pratultandon/recipe-nlg-gpt2")

ingredients = ['Tomatoes', 'Cheese', 'basil', 'yeast']

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
    for length in range(len(ingredients), 0, -1):
        subarray = ingredients[:length]

        prompt = GeneratePrompt(subarray)

        # Tokenize input and generate text
        input_ids = tokenizer.encode(prompt, return_tensors="pt")
        output = model.generate(input_ids, max_length=200, num_return_sequences=1, no_repeat_ngram_size=2, top_k=50, temperature=0.5)

        # Decode generated text
        generated_text = tokenizer.decode(output[0], skip_special_tokens=False)
        recipe_end_index = generated_text.find("<RECIPE_END>")

        # parse the data
        parsedData = parseMarkers(generated_text[:recipe_end_index])
        final_generated_text.append(parsedData)

        
    print(final_generated_text)
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

    return recipe    