import streamlit as st
from helper import *


def main():
    st.set_page_config(page_title="Researcher...",page_icon=':parrot:',layout="wide")
    st.header("Generate a article :parrot:")
    query=st.text_input("Enter a topic")
    if query:
        with st.spinner(f"Generating article for topic {query}"):
            search_result=search_serp(query=query)
            best_picks=pick_bestUrl(search_result,query)
            data=extract_url_content(best_picks)
            summary=create_summary(data,query)
            article=generate_article(summary,query)
        with st.expander("Best URLs"):
            st.info(best_picks)
        with st.expander("Summaries of all articles"):
            st.info(summary)
        with st.expander("Article: "):
            st.info(article)
        st.success("Done")
            
    # res=search_serp("Pakistan Cricket Team")
    
    # best=pick_bestUrl(res,"Pakistan Cricket Team")
    # url_db=extract_url_content(best)
    
    
    # summary=create_summary(url_db,"Pakistan Cricket Team")
    # article=generate_article(summary, "Pakistan Cricket Team")
    
    # print(summary)
    







if __name__ == "__main__":
    main()