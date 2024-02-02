from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import os

#load environment variables
load_dotenv()


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


# create 'embeddings' model that is responsible for converting chunks of texts to vector.
embeddings = AzureOpenAIEmbeddings(
    azure_deployment=embedding_model_deployment_name,
    openai_api_version=api_version,
    chunk_size=1
)


dataFolderPath = "./pdf_docs/"

# This variable will contain the path of pdf_doc (to be queried) after the 'data' folder inside current folder.
user_instructions_about_fileName_input = """Enter pdf file name to be indexed for question answering, along with extension '.pdf' (part of file path after 'data/' folder is to be passed): \n
For ex:
- If you have a file in the path as: './pdf_docs/testFolder/test_doc.pdf', your input should be 'testFolder/test_doc.pdf'
- If you have a file in the path as: './pdf_docs/test_doc2.pdf', your input should be 'test_doc2.pdf'
> """
fileName = input( user_instructions_about_fileName_input )

# Removing '/' or '\' signs used at the beginning of the file name by users
if fileName[0] in ('/', '\\'):
    fileName = fileName[1::]

completeFilePath = dataFolderPath + fileName

try:
    #use langchain PDF loader
    loader = PyPDFLoader( completeFilePath )
    
    #split the document into chunks
    pages = loader.load_and_split()
    
    #Use Langchain to create the embeddings using text-embedding-ada-002
    db = FAISS.from_documents(documents=pages, embedding=embeddings)
    
    #save the embeddings into FAISS vector store inside the './faiss_vector_dbs/' folder
    db.save_local( f"./faiss_vector_dbs/{ fileName.replace('.pdf', '') }_faiss_index" )

except ValueError:
    print("Document with specified name does not exist in the directory. Check file name and path carefully!")
else:
    print("FAISS index generated successfully! The document is ready for question-answer!")


input("Press Enter to exit...")