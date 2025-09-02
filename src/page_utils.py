import streamlit as st

def sidebar_width():
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                width: 700mm !important; # Set the width to your desired value
            }
        </style>
        """,
        unsafe_allow_html=True,
    )