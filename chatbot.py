import openai 
import streamlit as st
from streamlit_chat import message
import azure.cognitiveservices.speech as speechsdk

# Code Source: https://github.com/marshmellow77/streamlit-chatgpt-ui/blob/main/app.py

# Setting page title and header
st.set_page_config(page_title="OAI", page_icon=":robot_face:")
st.markdown("<h1 style='text-align: center;'>OAI - A Stealth Mode Project</h1>", unsafe_allow_html=True)

openai.api_key = st.secrets["OPENAI_SECRET_KEY"]

# Initial system message
initial_system_message = f"""
Dein Name ist Kasper.
Du bist Mitarbeiter im Verkauf bei Amaseo, \
einem Amazon und Google Partner Unternehmen.
Du bist gerade in einem Telefongespräch mit \
einem potenziellen Kunden, den du angerufen hast.
Du bist ein aktiver und sehr erfolgreicher Verkäufer.
Dies lässt du den Kunden aber nicht wissen.
Deine Antworten sind kurz, prägnant und effektiv.
Du sprichst den Kunden stets mit 'Sie' an.
Dein Ziel ist es, den Kunden davon zu überzeugen, \
einem Follow-up Meeting mit einem der Produktexperten \
bei Amaseo zuzustimmen.
Du erhältst Antworten, Fragen und Einwände von dem \
potenziellen Kunden.
Du gibst freundliche und aufschlussreiche Antworten \
und stellst sinnhafte Nachfragen falls nötig.
Hier sind relevante Informationen zu Amaseo:
Name: Amaseo GmbH
Standort: Hamburg, Deutschland
Erfahrung: Insgesamt mehr als 10 Jahre Erfahrung
Angebot: Werbe- und Kampagnenoptimierung für \
Amazon und Google mit Fokus auf E-Commerce Unternehmen.
Vorteile für Kunden: Erfolgsbasierte Preisbildung, \
im Durchschnitt bis zu 20% mehr Umsatz bei \
gleichbleibenden Werbeausgaben, höhere Sichtbarkeit \
auf Amazon oder Google.
"""

# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": f"{initial_system_message}"}
    ]
if 'model_name' not in st.session_state:
    st.session_state['model_name'] = []
if 'cost' not in st.session_state:
    st.session_state['cost'] = []
if 'total_tokens' not in st.session_state:
    st.session_state['total_tokens'] = []
if 'total_cost' not in st.session_state:
    st.session_state['total_cost'] = 0.0

# Sidebar - let user choose model, show total cost of current conversation, and let user clear the current conversation
st.sidebar.title("Sidebar")
model_name = st.sidebar.radio("Choose a model:", ("GPT-3.5", "GPT-4"))
counter_placeholder = st.sidebar.empty()
counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")
clear_button = st.sidebar.button("Clear Conversation", key="clear")

# Map model names to OpenAI model IDs
if model_name == "GPT-3.5":
    model = "gpt-3.5-turbo"
else:
    model = "gpt-4"

# reset everything
if clear_button:
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['messages'] = [
        {"role": "system", "content": f"{initial_system_message}"}
    ]
    st.session_state['number_tokens'] = []
    st.session_state['model_name'] = []
    st.session_state['cost'] = []
    st.session_state['total_cost'] = 0.0
    st.session_state['total_tokens'] = []
    counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")

# generate a response
def generate_response(prompt):
    st.session_state['messages'].append({"role": "user", "content": prompt})

    completion = openai.ChatCompletion.create(
        model=model,
        messages=st.session_state['messages']
    )
    response = completion.choices[0].message.content
    st.session_state['messages'].append({"role": "assistant", "content": response})

    print(st.session_state['messages'])
    total_tokens = completion.usage.total_tokens
    prompt_tokens = completion.usage.prompt_tokens
    completion_tokens = completion.usage.completion_tokens
    return response, total_tokens, prompt_tokens, completion_tokens

# Azure Text-to-Speech
speech_config = speechsdk.SpeechConfig(subscription=st.secrets["AZURE_SPEECH_KEY"], region=st.secrets["AZURE_REGION_KEY"])
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

# The language of the voice that speaks.
speech_config.speech_synthesis_voice_name='de-DE-KasperNeural'
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

def speak_text(speech_synthesizer, text):
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(cancellation_details.error_details))
                print("Did you set the speech resource key and region values?")
    return speech_synthesis_result

# container for chat history
response_container = st.container()
# container for text box
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You:", key='input', height=100)
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        output, total_tokens, prompt_tokens, completion_tokens = generate_response(user_input)
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)
        st.session_state['model_name'].append(model_name)
        st.session_state['total_tokens'].append(total_tokens)

        # from https://openai.com/pricing#language-models
        if model_name == "GPT-3.5":
            cost = total_tokens * 0.002 / 1000
        else:
            cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000

        st.session_state['cost'].append(cost)
        st.session_state['total_cost'] += cost

        # synthesize text-to-speech
        # speak_text(speech_synthesizer, output)

if st.session_state['generated']:
    with response_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
            message(st.session_state["generated"][i], key=str(i))
            st.write(
                f"Model used: {st.session_state['model_name'][i]}; Number of tokens: {st.session_state['total_tokens'][i]}; Cost: ${st.session_state['cost'][i]:.5f}")
            counter_placeholder.write(f"Total cost of this conversation: ${st.session_state['total_cost']:.5f}")