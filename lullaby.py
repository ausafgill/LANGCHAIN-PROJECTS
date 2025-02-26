import os
from dotenv import find_dotenv, load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
import streamlit as st

load_dotenv(find_dotenv())

# Initialize Google Generative AI
llm_model = "gemini-2.0-flash-exp" 
gen_ai = GoogleGenerativeAI(model=llm_model, temperature=0.7) 

# Function to generate a lullaby
def generate_lullaby(location, name, language):
    # Step 1: Generate the story
    story_template = """ 
        As a children's book writer, please come up with a simple and short (90 words)
        lullaby based on the location {location} and the main character {name}.
        
        STORY:
    """
    story_prompt = PromptTemplate(input_variables=["location", "name"], template=story_template)
    story_chain = story_prompt | gen_ai

    # Step 2: Translate the story
    translate_template = """
    Translate the following story into {language}. Make sure 
    the language is simple and fun.

    STORY: {story}

    TRANSLATION:
    """
    translate_prompt = PromptTemplate(input_variables=["story", "language"], template=translate_template)
    translate_chain = translate_prompt | gen_ai

    # Combine the chains using RunnableLambda and RunnablePassthrough
    full_chain = (
        RunnablePassthrough.assign(story=lambda inputs: story_chain.invoke({"location": inputs["location"], "name": inputs["name"]}))
        | RunnableLambda(lambda inputs: {"story": inputs["story"], "language": inputs["language"]})
        | RunnableLambda(lambda inputs: {"translated": translate_chain.invoke({"story": inputs["story"], "language": inputs["language"]}), **inputs})
    )

  
    response = full_chain.invoke({"location": location, "name": name, "language": language})
    return response


def main():
    st.set_page_config(page_title="Generate Children's Lullaby", layout="centered")
    st.title("Let AI Write and Translate a Lullaby for You 📖")
    st.header("Get Started...")

    location_input = st.text_input(label="Where is the story set?")
    main_character_input = st.text_input(label="What's the main character's name")
    language_input = st.text_input(label="Translate the story into...")

    submit_button = st.button("Submit")
    if location_input and main_character_input and language_input:
        if submit_button:
            with st.spinner("Generating lullaby..."):
                response = generate_lullaby(
                    location=location_input,
                    name=main_character_input,
                    language=language_input
                )

                with st.expander("English Version"):
                    st.write(response['story'])
                with st.expander(f"{language_input} Version"):
                    st.write(response['translated'])

            st.success("Lullaby Successfully Generated!")


if __name__ == '__main__':
    main()