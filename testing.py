from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load pre-trained model and tokenizer
model = GPT2LMHeadModel.from_pretrained("gpt2")
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# Input prompt
prompt = "Give me a description of the food pizza, all the ingredients needed to make it, and more about how to make it."

# Tokenize input and generate text
input_ids = tokenizer.encode(prompt, return_tensors="pt")
output = model.generate(input_ids, max_length=100, num_return_sequences=1, no_repeat_ngram_size=2, top_k=50)

# Decode generated text
generated_text = tokenizer.decode(output[0], skip_special_tokens=True)

print(generated_text)