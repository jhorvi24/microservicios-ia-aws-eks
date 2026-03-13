
#Dashboard usando streamlit para ingreso de texto y analisis de sentimiento

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Sentiment Analysis Dashboard", page_icon=":bar_chart:", layout="wide")

st.title("Sentiment Analysis Dashboard")
st.markdown("### AI Analysis Sentiment")


#Get URL from enviroment variables
NLP_SERVICE_URL = os.getenv("NLP_SERVICE_URL", "http://localhost:5000")
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8001")



#Input text
with st.sidebar:
    st.header("Submit new insight")
    text_input = st.text_area("Enter text to analyze:", placeholder="Enter customer text... ")

    if st.button("Analyze Sentiment", type="primary"):
        if text_input:
            with st.spinner("Analyzing..."):
                #Call NLP service
                try:
                    response = requests.post(
                        f"{NLP_SERVICE_URL}/analyze", 
                        json={"text": text_input},
                        timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Analysis complete!")
                        st.write(f"**Sentiment:** {result['sentiment']}")
                        st.write(f"**Confidence:** {result['confidence']}")
                    else:
                        st.error("Error analyzing sentiment")
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            st.warning("Please enter some text")

#Main dashboard

st.header("Recent Analyses")

try:
    response = requests.get(f"{STORAGE_SERVICE_URL}/results", timeout=30)
    if response.status_code == 200:
        analyses = response.json()
        if analyses:
            df = pd.DataFrame(analyses)
            #df['timestamp'] = pd.to_datetime(df['timestamp'])
            #df = df.sort_values('timestamp', ascending=False)
            #st.dataframe(df[['text', 'sentiment', 'confidence', 'timestamp']], use_container_width=True)
            # Mostrar métricas rápidas
            col1, col2 = st.columns(2)
            col1.metric("Total Análisis", len(df))
            col2.metric("Promedio Confianza", f"{df['score'].mean():.2f}")

            # Mostrar tabla
            st.subheader("Historial de Análisis")
            st.dataframe(df[['created_at', 'text', 'label', 'score']])
            
            # Gráfico simple
            st.subheader("Distribución de Sentimientos")
            st.bar_chart(df['label'].value_counts())
        else:
            st.info("No analyses available yet.")
    else:
        st.error("Error fetching analyses")
except Exception as e:
    st.error(f"Connection error: {e}")
st.markdown("---")
st.caption("NLP Service Dashboard - Real-time sentiment analysis")