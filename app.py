import streamlit as st
import pandas as pd

# 1. Set up the page
st.set_page_config(page_title="Plastic Monitoring Finder", layout="wide")
st.title("🌊 Plastic Monitoring Method Recommender")
st.write("Select your constraints below to find the best monitoring method for your project.")

# 2. Load the data
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

df = load_data()

# 3. Create a sidebar for user filters
st.sidebar.header("Filter your needs:")

# Example Filter: Investment Cost
cost_filter = st.sidebar.multiselect(
    "Acceptable Initial Investment Cost:",
    options=df["Initial Investment Cost"].unique(),
    default=df["Initial Investment Cost"].unique()
)

# 4. Filter the dataframe based on user selection
filtered_df = df[df["Initial Investment Cost"].isin(cost_filter)]

# 5. Display the results
st.subheader("Recommended Methods")
st.dataframe(filtered_df)
