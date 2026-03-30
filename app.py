import streamlit as st
import pandas as pd

# Set up the page
st.set_page_config(page_title="Plastic Monitoring Recommender", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_labels_matrix():
    # Load the labels matrix and rename the first unnamed column to 'Method'
    df = pd.read_csv("labels.csv")
    df.rename(columns={df.columns[0]: 'Method'}, inplace=True)
    return df

@st.cache_data
def load_properties():
    # Load the properties data we created earlier
    return pd.read_csv("data.csv")

labels_df = load_labels_matrix()
properties_df = load_properties()

# Extract all available labels (skip the 'Method' column)
available_labels = list(labels_df.columns)[1:]

st.title("🌊 Plastic Monitoring Method Recommender")

# ==========================================
# PART 1: RECOMMENDATION ENGINE (VBA Logic)
# ==========================================
st.header("Part 1: Find the Best Method")
st.write("Select your constraints below to get recommendations based on your needs.")

# This replaces the ListBox 1 & 2 logic from VBA
selected_labels = st.multiselect(
    "Select your requirements (Labels):",
    options=available_labels
)

if st.button("Get Recommendations"):
    highly_rec = []
    good_fit = []
    possible_fit = []
    not_rec = []

    # Check for exclusion flags
    has_open_water = any("Open water" in label for label in selected_labels)
    has_submerged = any("Submerged items" in label for label in selected_labels)

    # Loop through each method in the matrix (replaces the 'For methodRow = 2 To 7' loop)
    for index, row in labels_df.iterrows():
        method_name = str(row['Method'])
        match_count = 0
        exclude_reason = ""

        # Count how many selected labels have an "x" for this method
        for label in selected_labels:
            cell_value = str(row[label]).strip().lower()
            if cell_value == 'x':
                match_count += 1

        # --- LOGIC: Apply Exclusion Rules ---
        # Rule 1: No Bridge
        bridge_methods = ["Visual counting from bridge", "Bridge-mounted camera sensor", "Surface trawling from bridge", "Net trawling from bridge"]
        if has_open_water and any(m in method_name for m in bridge_methods):
            exclude_reason = "(Requires Bridge)"

        # Rule 2: Cannot see submerged items
        visual_methods = ["Visual counting from bridge", "Visual counting from boat"]
        if has_submerged and any(m in method_name for m in visual_methods):
            if exclude_reason == "":
                exclude_reason = "(Visual methods cannot see submerged items)"
            else:
                exclude_reason = "(Requires Bridge & Cannot see submerged items)"

        # --- LOGIC: Sort into Buckets ---
        if exclude_reason != "":
            not_rec.append(f"**{method_name}**\n\n*{exclude_reason}*")
        else:
            if match_count >= 4:
                highly_rec.append(f"**{method_name}**")
            elif match_count == 3:
                good_fit.append(f"**{method_name}**")
            elif match_count >= 1:
                possible_fit.append(f"**{method_name}**")

    # Display the sorted buckets neatly using Streamlit columns
    st.markdown("### Recommendations")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.success("🌟 **HIGHLY RECOMMENDED**\n\n(4+ matches)")
        for m in highly_rec: st.info(m)
    with col2:
        st.info("✅ **Good Fit**\n\n(3 matches)")
        for m in good_fit: st.success(m)
    with col3:
        st.warning("⚠️ **Possible Fit**\n\n(1-2 matches)")
        for m in possible_fit: st.warning(m)
    with col4:
        st.error("❌ **NOT RECOMMENDED**\n\n(Rule Exclusions)")
        for m in not_rec: st.error(m)


st.divider() # Adds a nice horizontal line

# ==========================================
# PART 2: METHOD COMPARISON TOOL
# ==========================================
st.header("Part 2: Compare Methods")
st.write("Select up to two methods to compare their specific properties side-by-side.")

all_methods = properties_df['Method'].tolist()

# Limit selection to exactly 2 items for a clean comparison
compare_selection = st.multiselect(
    "Select methods to compare:",
    options=all_methods,
    max_selections=2
)

if len(compare_selection) > 0:
    if st.button("Compare Methods"):
        # Filter the properties dataset to only the selected methods
        compare_df = properties_df[properties_df['Method'].isin(compare_selection)]
        
        # Transpose the table (flip rows and columns) to make it look like an online shop comparison
        compare_df = compare_df.set_index('Method').T
        
        # Display the comparison table
        st.dataframe(compare_df, use_container_width=True)
