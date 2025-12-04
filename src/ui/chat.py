import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.rag.engine import QueryEngine

st.set_page_config(page_title="Erica - AI Tutor", page_icon="🎓")

st.title("🎓 Erica - Your AI Tutor")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize engine
if "engine" not in st.session_state:
    with st.spinner("Initializing Knowledge Base..."):
        try:
            st.session_state.engine = QueryEngine()
            st.success("Ready!")
        except Exception as e:
            st.error(f"Failed to initialize engine: {e}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask me anything about the AI course..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate response
    with st.chat_message("assistant"):
        if "engine" in st.session_state:
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.engine.query(prompt)
                    
                    # Handle both string (legacy) and dict responses
                    if isinstance(result, dict):
                        response = result["answer"]
                        context = result["context"]
                        concepts = result.get("concepts", [])
                    else:
                        response = result
                        context = None
                        concepts = []
                        
                    st.markdown(response)
                    
                    # Show context in expander
                    with st.expander("🔍 View RAG Context"):
                        if concepts:
                            st.write(f"**Identified Concepts:** {', '.join(concepts)}")
                        if context:
                            st.text(context)
                        else:
                            st.warning("No context retrieved from the Knowledge Graph.")
                            
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error generating response: {e}")
        else:
            st.error("Engine not initialized.")
