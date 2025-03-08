import os
from dotenv import load_dotenv,find_dotenv
import json
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_community.vectorstores import FAISS
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.text_splitter import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
import json
from langchain.prompts import PromptTemplate
load_dotenv(find_dotenv())
llm_model = "gemini-2.0-flash-exp" 
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gen_ai = GoogleGenerativeAI(model=llm_model, temperature=0.7) 
chat_model=ChatGoogleGenerativeAI(model=llm_model,temperature=0.7)

embeddings=GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=GOOGLE_API_KEY)

#Serp func to look for Links
def search_serp(query):
    search=GoogleSerperAPIWrapper(k=5,type="search")
    json_res=search.results(query)
    print(f"Response=====>, {json_res}")
    return json_res

#llm gives me best urls

def pick_bestUrl(json_res, query):
    res_str = json.dumps(json_res)  # Convert JSON response to string
    
    template = """ 
      You are a world-class journalist, researcher, tech expert, software engineer, developer, and online course creator.
      You excel at finding the most interesting, relevant, and useful articles on various topics.
      
      QUERY RESPONSE: {res_str}
      
      Above is the list of search results for the query "{query}".
      
      Please choose the best 3 articles from the list and return ONLY an array of the URLs.  
      The URLs should be extracted from the 'organic' or 'results' field of the JSON response.
      Do not include anything else—return ONLY an array of the URLs. 
      Ensure the articles are recent and not too old.
      If a URL is invalid, return ["www.google.com"].
    """

    prompt_template = PromptTemplate(input_variables=["res_str", "query"], template=template)

    chain = prompt_template | chat_model  

    urls = chain.invoke({"res_str": res_str, "query": query})  

    if hasattr(urls, "content"):
        urls = urls.content

    print(f"LLM Response: {urls}")  # Log the LLM response

    try:
        url_list = json.loads(urls) 
    except json.JSONDecodeError:
        # Fallback: Manually extract URLs from the search results
        url_list = []
        if isinstance(json_res, dict) and 'organic' in json_res:
            for result in json_res['organic'][:3]:  # Take top 3 results
                if 'link' in result:
                    url_list.append(result['link'])
        if not url_list:
            url_list = ["www.google.com"]

    return url_list
#get content from each url and create vectordb
def extract_url_content(urls):
    urls = [f"https://{url}" if not url.startswith(("http://", "https://")) else url for url in urls]

    loader=UnstructuredURLLoader(urls=urls)
    data=loader.load()
    text_splitter=CharacterTextSplitter(separator='\n',
                                        chunk_size=1000,
                                        chunk_overlap=200,
                                        length_function=len
                                        )
    docs=text_splitter.split_documents(data)
    if not docs:
      raise ValueError("No valid documents found for embedding!")

    db = FAISS.from_documents(docs, embeddings)

    
    return db

def create_summary(db,query,k=4):
    docs=db.similarity_search(query,k=k)
    docs_page_content="".join([d.page_content for d in docs])
    template = """
       {docs}
        As a world class journalist, researcher, article, newsletter and blog writer, 
        you will summarize the text above in order to create a 
        newsletter around {query}.
        This newsletter will be sent as an email.  The format is going to be like
        Tim Ferriss' "5-Bullet Friday" newsletter.
        
        Please follow all of the following guidelines:
        1/ Make sure the content is engaging, informative with good data
        2/ Make sure the conent is not too long, it should be the size of a nice newsletter bullet point and summary
        3/ The content should address the {query} topic very well
        4/ The content needs to be good and informative
        5/ The content needs to be written in a way that is easy to read, digest and understand
        6/ The content needs to give the audience actinable advice & insights including resouces and links if necessary
        
        SUMMARY:
    """
    prompt_template=PromptTemplate(input_variables=["docs","query"],template=template)
    chain=prompt_template|chat_model
    summary=chain.invoke({"docs":docs_page_content,"query":query})
    return summary.content
    
def generate_article(summary,query):
    summary_str=str(summary)
    template = """
    {summary_str}
        As a world class journalist, researcher, article, newsletter and blog writer, 
        you'll use the text above as the context about {query}
        to write an excellent newsletter to be sent to subscribers about {query}.
        
        This newsletter will be sent as an email.  The format is going to be like
        Tim Ferriss' "5-Bullet Friday" newsletter.
        
        Make sure to write it informally - no "Dear" or any other formalities.  Start the newsletter with
        `Hi All!
          Here is your weekly dose of the Tech Newsletter, a list of what I find interesting
          and worth and exploring.`
          
        Make sure to also write a backstory about the topic - make it personal, engaging and lighthearted before
        going into the meat of the newsletter.
        
        Please follow all of the following guidelines:
        1/ Make sure the content is engaging, informative with good data
        2/ Make sure the conent is not too long, it should be the size of a nice newsletter bullet point and summary
        3/ The content should address the {query} topic very well
        4/ The content needs to be good and informative
        5/ The content needs to be written in a way that is easy to read, digest and understand
        6/ The content needs to give the audience actinable advice & insights including resouces and links if necessary.
        
        If there are books, or products involved, make sure to add amazon links to the products or just a link placeholder.
        
        As a signoff, write a clever quote related to learning, general wisdom, living a good life.  Be creative with this one - and then,
        Sign with "Ausaf Gill 
          - Learner"
        
        NEWSLETTER-->:
    """
    prompt=PromptTemplate(input_variables=['summary_str','query'],template=template)
    chain=prompt|chat_model
    article=chain.invoke({'summary_str':summary_str,'query':query})
    return article.content
    