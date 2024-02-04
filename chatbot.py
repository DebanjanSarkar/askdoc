from dotenv import load_dotenv
import os
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate

#load environment variables
load_dotenv()

"""
    API Configuration
----------------------------
"""

# Azure OpenAI resource API key and version
api_key = os.getenv("AZURE_OPENAI_KEY")
api_version = os.getenv("API_VERSION")

# Azure endpoint at which the resource is deployed
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

# Deployment name of the Azure OpenAI resources
llm_deployment_name = os.getenv("AZURE_GPTTURBO_DEPLOYMENT_NAME")
embedding_model_deployment_name = os.getenv("AZURE_OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME")


os.environ["OPENAI_API_TYPE"]     = "azure"
os.environ["OPENAI_API_VERSION"]  = api_version
os.environ["OPENAI_API_KEY"]      = api_key



"""
    Functions and __main__ block
-----------------------------------
"""

# Use this function to fetch answer if the questions need not needs previous contexts and questions to be remembered.
# This takes up less tokens each time
def ask_question(qa, question):
    result = qa({"query": question})
    print("Question:", question)
    print("Answer:", result["result"])


# To make the chatbot remember the context of entire conversation, use this function.
# Using this function in loop, number of token utilization for each request increases subsequently.
def ask_question_with_context(qa, question, chat_history):
    result = qa({"question": question, "chat_history": chat_history})
    print("Answer:", result["answer"])
    # Use the below line of code if you want the model to be aware of only last question and answer.
    chat_history = [(question, result["answer"])]
    # Use the below line of code if you want the model to be aware of entire conversation. Token utilization grows up by a huge size after some conversation
    # chat_history = chat_history.append( (question, result["answer"]) )    
    return chat_history



# Initialize gpt-35-turbo and our embedding model
llm = AzureChatOpenAI(
    openai_api_version=api_version,
    azure_deployment=llm_deployment_name,
)

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=embedding_model_deployment_name,
    openai_api_version=api_version,
    chunk_size=1
)


# This variable will contain the path of pdf_doc (to be queried) after the 'data' folder inside current folder.
user_instructions_about_fileName_input = """Enter pdf file name which you want to question, along with extension '.pdf' (part of file path after 'data/' folder is to be passed): \n
For ex:
- If you have a file in the path as: './pdf_docs/testFolder/test_doc.pdf', your input should be 'testFolder/test_doc.pdf'
- If you have a file in the path as: './pdf_docs/test_doc2.pdf', your input should be 'test_doc2.pdf'
> """
# Asks user which pdf coument is to be queried
fileName = input( user_instructions_about_fileName_input )

# Removing '/' or '\' signs used at the beginning of the file name by users
if fileName[0] in ('/', '\\'):
    fileName = fileName[1::]

try:
    #load the faiss vector store we saved into memory
    vectorStore = FAISS.load_local( f"./faiss_vector_dbs/{ fileName.replace('.pdf', '') }_faiss_index" , embeddings)
    
    #use the faiss vector store we saved to search the local document
    retriever = vectorStore.as_retriever(search_type="similarity", search_kwargs={"k":2})
    
    QUESTION_PROMPT = PromptTemplate.from_template("""Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, according to the format stated in the follow up question.
    
    Chat History:
    {chat_history}
    Follow Up Input: {question}
    Standalone question:
    """)
    
    qa = ConversationalRetrievalChain.from_llm(llm=llm,
                                            retriever=retriever,
                                            condense_question_prompt=QUESTION_PROMPT,
                                            return_source_documents=True,
                                            verbose=False)
    
    
    chat_history = []
    while True:
        query = input('User: ')
        if query in ('q', 'quit', 'exit', 'close'):
            break
        chat_history = ask_question_with_context(qa, query, chat_history)
        print("===============================================================================================")
except:
    print("Either the file does not exist, or it has not been indexed! Check for the correct file, index it using indexer, and then retry...")

