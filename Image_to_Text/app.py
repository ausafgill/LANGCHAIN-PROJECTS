import os
from dotenv import find_dotenv, load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
from langchain.prompts import PromptTemplate
import requests
from PIL import Image
import io

import streamlit as st
load_dotenv(find_dotenv())
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
HUGGING_FACE_API=os.getenv("HUGGING_FACE_API")
chat=ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp",temperature=0.7)
from transformers import (
    pipeline,
)  


#image_to_text
def image_to_text(upload_file):
    pipe = pipeline("image-to-text", model="Salesforce/blip-image-captioning-large", max_new_tokens=1000)

    # Convert the uploaded file to a PIL image
    image = Image.open(io.BytesIO(upload_file.getvalue()))

    # Pass the PIL image to the pipeline
    text = pipe(image)[0]['generated_text']
    return text
    

def text_to_speech(text):
    API_URL = "https://router.huggingface.co/hf-inference/models/facebook/fastspeech2-en-ljspeech"
    headers = {"Authorization": f"Bearer {HUGGING_FACE_API} "}
    payload = {
        "inputs": text,
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content

def generate_recipe(ingredients):
    template = """
    You are an extremely knowledgeable nutritionist, bodybuilder, and chef who also knows
    everything about the best quick, healthy recipes, including both Western and Desi (South Asian) dishes.
    You specialize in providing recipes that keep people lean, help them build muscle, and promote fat loss.

    You have trained top-performing athletes in bodybuilding and maintaining an incredible physique.
    You also understand how to help people who have limited time or ingredients by suggesting 
    meals that are quick, easy, and healthy.

    Your job is to assist users with finding the best recipes and cooking instructions 
    depending on the available ingredients:
    0/ {ingredients}

    When generating recipes, follow these guidelines:
    - Answer confidently and concisely.
    - Consider a time constraint of 5-10 minutes when suggesting recipes.
    - If {ingredients} are fewer than 3, feel free to suggest a few complementary ones 
      to make a well-balanced meal.
    - Include Desi recipes such as dal, sabzi, paratha, chaat, or protein-rich South Asian dishes 
      when relevant.

    **Ensure that the response is formatted as follows:**
    - **Meal Name** (bold, new line)
    - **Best for**: (bold, specify category, e.g., muscle gain, weight loss, quick meal)
    
    - **Preparation Time**: (Header)
    
    - **Difficulty**: (bold)
      Easy
    
    - **Ingredients**: (bold)
      List all ingredients, including any necessary Desi spices.
    
    - **Kitchen Tools Needed**: (bold)
      List required kitchen tools.
    
    - **Instructions**: (bold)
      Provide clear, step-by-step instructions.
    
    - **Macros**: (bold)
      - Total calories
      - List each ingredient's calories
      - Provide macronutrient breakdown (protein, carbs, fats)

    Please ensure the instructions are **brief, easy to follow, and step-by-step**.
    """

    prompt_template=PromptTemplate(input_variables=['ingredients'],template=template)
    chain=prompt_template|chat
    response=chain.invoke({"ingredients":ingredients})
    return response.content



def main():
    st.title("Image to Recipe 🍺")
    st.header("Upload an image and get a recipe")
    upload_file=st.file_uploader("Choose an image",type=['png','jpg'],)
    if upload_file is not None:
        print(upload_file)
        file_bytes=upload_file.getvalue()
        with open(upload_file.name,"wb") as file:
            file.write(file_bytes)
        st.image(upload_file,use_container_width=True,caption="The uploaded Image")
        ingredients=image_to_text(upload_file)
        audio = text_to_speech(ingredients)


        recipe=generate_recipe(ingredients)
        with st.expander("Ingredients"):
            st.write(ingredients)
        with st.expander("Recipe"):
            st.write(recipe)
        if audio:
                st.audio(audio, format="audio/flac")
        else:
            st.error("Failed to generate audio.")
        
        


  

if __name__ == "__main__":
    main()