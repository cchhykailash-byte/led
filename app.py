import streamlit as st

st.set_page_config(
    page_title="My First Streamlit App",
    page_icon="🚀",
    layout="centered"
)

st.title("🚀 Hello Streamlit!")

st.success("Congratulations! Your Render deployment is working.")

name = st.text_input("Enter your name")

if name:
    st.write(f"Hello, **{name}** 👋")

if st.button("Click Me"):
    st.balloons()
    st.success("Button clicked successfully!")
