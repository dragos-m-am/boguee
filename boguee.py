#from dotenv import load_dotenv
import os
import streamlit as st
from openai import OpenAI
import json
import random

def questions(filee, n):
    with open(filee) as fd:

        json_questions = json.load(fd)
        json_short=random.sample(json_questions, n)
        json_text=json.dumps(json_short)
        return json_text

questions = questions('trivia1.json', 5)

instruction1 = (

"Your name is Boguee, a text based game maker. "

"The game that you are playing is called trivia and consists of asking questions to the user, getting back answers and evaluating the correctness of the answers. You are not playing yourself.  You are expressing yourself in short and punchy lines. The shorter the better. Plus emojis."

"Introduction"
"When we start the conversation, you will introduce yourself and welcome the user to the game!"
"After that ask for the user name;" 

"Instructions to play the game"
"1. The questions that you will ask the user are the following:"
)

instruction2 = """
1. You will display the first question 
2. You will display the three answers for the selected question delimited by commas, on a separate row
3. You will ask the user to answer
4. You will reply if the user's answer is correct. 
5. The user can reply with numbers 1,2,3 representing 1 the first answer, 2 the second one and 3 the third answer.
6. If the user answers with none of the answers or a a different one, you will tell the user that she is wrong.
7. You will repeat the same for each of the next questions

In the end you will present the summary:
- list each question and mention if the result was correct or not
- the total score

Conditions
- You will only use the questions mentioned in this prompt.
- Try to deduce the answers, if customers answer with words that are similar. E.g. if the user can answer with Victoria for Victoria's secret.
- Do not use general GPT knowledge.
- If you receive any question that is NOT related to this trivia game, you will answer - I am just a poor trivia game maker, I won't be able to help you with that.-
"""

instructions = instruction1 + questions + instruction2


class Config:
    """Singleton configuration class for environment variables."""
    #load_dotenv()

    API_KEY = st.secrets["open_ai"] 
    ASSISTANT_KEY = st.secrets["assistant"]
    OPENAI_MODEL = "gpt-4o"
    #ASSISTANT_KEY = os.getenv("ASSISTANT_KEY")
    PAGE_TITLE = "Boguee - a glamourous text based game maker!"
    WELCOME_MESSAGE = "Hello, I'm your Boguee. I am here and I am in  the mood to play! Grrrr!"
    INSTRUCTIONS = instructions
    USER_PROMPT = "Say 'Hello' to me!"
    BEGIN_MESSAGE = "Let's rumble."
    EXIT_MESSAGE = "Turn your back to poor Boguee"
    START_CHAT_BUTTON = "Make the game!"
    #OPENAI_MODEL = os.getenv("OPENAI_MODEL")
    LOGO="boguee_logo.png"


def initialize_openai_client():
    """Initializes and returns the OpenAI client along with the assistant object."""
    client = OpenAI(api_key=Config.API_KEY)
    assistant = client.beta.assistants.retrieve(Config.ASSISTANT_KEY)
    return client, assistant

def setup_streamlit_ui():
    """Configures Streamlit's page and displays initial UI components."""
    st.set_page_config(page_title=Config.PAGE_TITLE, page_icon=":speech_balloon:")
    apply_custom_css()
    #display_markdown_content(Config.DISCLAIMER)
    if os.path.isfile(Config.LOGO):
     st.image(Config.LOGO, width=180)
    st.title(Config.PAGE_TITLE)
    st.write(Config.WELCOME_MESSAGE)

def apply_custom_css():
    """Applies custom CSS to hide default Streamlit elements and adjust the layout."""
    custom_css = """
        <style>
            .reportview-container {margin-top: -2em;}
            #MainMenu, .stDeployButton, footer, #stDecoration {visibility: hidden;}
            html, body, [class*="css"] {font-family: 'Verdana', sans-serif; font-size: 18px;font-weight: 500; color: #091747;
}
        </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def display_markdown_content(file_path):
    """Reads and displays markdown content from a specified file."""
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        st.markdown(content, unsafe_allow_html=True)

def initialize_chat_variables():
    """Initializes necessary chat variables in Streamlit's session state."""
    defaults = {"start_chat": False, "thread_id": None, "messages": []}
    for key, default in defaults.items():
        st.session_state.setdefault(key, default)

def handle_chat_interaction(client, assistant):
    """Manages user interactions and chat logic."""
    if not st.session_state.get('start_chat', False):
        if st.button(Config.START_CHAT_BUTTON):
           start_new_chat_session(client)
           st.rerun()

    if 'start_chat' in st.session_state and st.session_state.start_chat:  
      if st.button(Config.EXIT_MESSAGE):
         reset_chat_session()
         st.rerun()
    if st.session_state.start_chat:
        display_chat_messages()
        user_input = st.chat_input(Config.USER_PROMPT)
        if user_input:
            process_and_display_chat_interaction(user_input, client, assistant)
    else:
      st.write(Config.BEGIN_MESSAGE)
      
def start_new_chat_session(client: OpenAI):
    """Begins a new chat session by creating a new thread."""
    st.session_state.start_chat = True
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

def reset_chat_session():
    """Resets the chat session to its initial state."""
    st.session_state["messages"] = []
    st.session_state["start_chat"] = False
    st.session_state["thread_id"] = None

def display_chat_messages():
    """Displays all chat messages stored in the session state."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def process_and_display_chat_interaction(user_input, client: OpenAI, assistant):
    """Processes the user input, fetches the assistant's response, and displays both in the chat."""
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id, role="user", content=user_input
    )

    with client.beta.threads.runs.create_and_stream(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant.id,
        model=Config.OPENAI_MODEL,
        instructions=Config.INSTRUCTIONS,
        # event_handler=EventHandler(streamlit),
    ) as stream:
        with st.chat_message("assistant"):
            response = st.write_stream(stream.text_deltas)
            stream.until_done()

    st.session_state.messages.append({"role": "assistant", "content": response})

# Main
if __name__ == "__main__":
    client, assistant = initialize_openai_client()
    # models = client.models.list()
    # for model in models:
    #     print(model)
    setup_streamlit_ui()
    initialize_chat_variables()
    handle_chat_interaction(client, assistant)
