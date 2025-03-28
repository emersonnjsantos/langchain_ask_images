
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st

# Adding History
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

import os, base64

# Sidebar for API Key
st.title("Chat Com Imagem")
with st.sidebar:
    st.title("Adicione sua chave de API ") 
    google_api_key = st.text_input("Chave de API Google Gemini", type="password")
    if not google_api_key:
        st.info("Digite sua chave de API Google Gemini para continuar")
        st.stop()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", google_api_key=google_api_key
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that can describe images."),
        MessagesPlaceholder(variable_name="chat_history"),
        (
            "human",
            [
                {"type": "text", "text": "{input}"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,""{image}",
                        "detail": "low",
                    },
                },
            ],
        ),
    ]
)

history = StreamlitChatMessageHistory()

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def process_image(file):
    with st.spinner("Processando imagem..."):
        data = file.read()
        file_name = os.path.join("./", file.name)
        with open(file_name, "wb") as f:
            f.write(data)
        image = encode_image(file_name)
        st.session_state.encoded_image = image
        st.success("Imagem codificada. Faça suas perguntas")

chain = prompt | llm

chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

def clear_history():
    if "langchain_messages" in st.session_state:
        del st.session_state["langchain_messages"]

uploaded_file = st.file_uploader("Carregue Sua Imagem: ", type=["jpg", "png"])
add_file = st.button("Enviar Imagem", on_click=clear_history)

if uploaded_file and add_file:
    process_image(uploaded_file)

for message in st.session_state.get("langchain_messages", []):
    role = "user" if message.type == "human" else "assistant"
    with st.chat_message(role):
        st.markdown(message.content)

question = st.chat_input("Your Question")
if question:
    with st.chat_message("user"):
        st.markdown(question)
    if "encoded_image" in st.session_state:
        image = st.session_state["encoded_image"]
        response = chain_with_history.stream(
            {"input": question, "image": image}, config={"configurable": {"session_id": "any"}}
        )
        with st.chat_message("assistant"):
            st.write_stream(response)
    else:
        st.error("Nenhuma imagem foi carregada. Carregue sua imagem primeiro.")
