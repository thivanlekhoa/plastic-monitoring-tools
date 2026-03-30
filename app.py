import streamlit as st
import pandas as pd

# Set up the page
st.set_page_config(page_title="Framework for Monitoring Plastic Export", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_labels_matrix():
    df = pd.read_csv("labels.csv")
    df.rename(columns={df.columns[0]: 'Method'}, inplace=True)
    return df

@st.cache_data
def load_properties():
    return pd.read_csv("data.csv")

labels_df = load_labels_matrix()
properties_df = load_properties()

st.title("🌊 Framework for Monitoring Plastic Export from Rivers to the Ocean")
st.write("Use this decision-support tool to identify the most suitable monitoring methods based on your project's specific constraints and goals.")

st.divider()

# ==========================================
# PART 1: RECOMMENDATION ENGINE
# ==========================================
st.header("Part 1: Find the Best Method")
st.write("Please fill out the categories below to filter the available monitoring methods.")

# --- CATEGORY 1: Data Needs ---
st.subheader("📊 1. Data Needs")
st.write("*Select the specific type of data you need to collect, such as counting items over time or analyzing physical properties, as well as the water depth you are targeting.*")
data_needs_options = [
    "Flux quantification (items/time)", 
    "Physical characterization (mass, polymer)", 
    "Floating (surface) items", 
    "Submerged items in water column"
]
data_needs = st.multiselect("Select your Data Needs:", options=data_needs_options)

# --- CATEGORY 2: Infrastructure ---
st.subheader("🏗️ 2. Infrastructure")
st.write("*Identify the physical structures and vessels you have access to at your monitoring location. This prevents recommending methods that require unavailable platforms.*")
infra_options = [
    "Bridge (fixed walkway) available", 
    "Open water (No existing infrastructure)", 
    "Vessel (boat) available", 
    "Anchored station available"
]
infrastructure = st.multiselect("Select your available Infrastructure:", options=infra_options)

# --- CATEGORY 3: Temporal Scope ---
st.subheader("⏱️ 3. Temporal Scope")
st.write("*Determine how frequently you plan to collect data. Some methods are built for quick, one-off checks, while others excel at long-term, continuous observation.*")
temporal_options = [
    "Continuous", 
    "Scheduled repeated surveys", 
    "One-time"
]
temporal = st.multiselect("Select your Temporal Scope:", options=temporal_options)

# --- CATEGORY 4: Resource Capacity ---
st.subheader("💰 4. Resource Capacity")
st.write("*Specify your financial and operational budget. This ensures the recommended tools align with your funding and team capabilities.*")
resource_options = [
    "Low budget", 
    "Medium budget (Vessel crew costs)", 
    "High budget (Tech investment)"
]
resource = st.multiselect("Select your Resource Capacity:", options=resource_options)

# Combine all selections into one list for the logic engine
selected_labels = data_needs + infrastructure + temporal + resource

# --- RECOMMENDATION LOGIC ---
if st.button("Get Recommendations", type="primary"):
    highly_rec = []
    good_fit = []
    possible_fit = []
    not_rec = []

    # Check for exclusion flags
    has_open_water = any("Open water" in label for label in selected_labels)
    has_submerged = any("Submerged items" in label for label in selected_labels)

    # Loop through each method in the matrix
    for index, row in labels_df.iterrows():
        method_name = str(row['Method'])
        match_count = 0
        exclude_reason = ""

        # Count how many selected labels have an "x" for this method
        for label in selected_labels:
            if label in labels_df.columns: # Safety check
                cell_value = str(row[label]).strip().lower()
                if cell_value == 'x':
                    match_count += 1

        # --- LOGIC: Apply Exclusion Rules ---
        bridge_methods = ["Visual counting from bridge", "Bridge-mounted camera sensor", "Surface trawling from bridge", "Net trawling from bridge"]
        if has_open_water and any(m in method_name for m in bridge_methods):
            exclude_reason = "(Requires Bridge)"

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

    # Display the sorted buckets neatly
    st.markdown("### 🏆 Your Recommendations")
    
    if len(selected_labels) == 0:
        st.warning("Please select at least one filter above to see recommendations.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.success("🌟 **HIGHLY RECOMMENDED**\n\n(4+ matches)")
            for m in highly_rec: st.info(m)
            if not highly_rec: st.write("*None*")
        with col2:
            st.info("✅ **Good Fit**\n\n(3 matches)")
            for m in good_fit: st.success(m)
            if not good_fit: st.write("*None*")
        with col3:
            st.warning("⚠️ **Possible Fit**\n\n(1-2 matches)")
            for m in possible_fit: st.warning(m)
            if not possible_fit: st.write("*None*")
        with col4:
            st.error("❌ **NOT RECOMMENDED**\n\n(Rule Exclusions)")
            for m in not_rec: st.error(m)
            if not not_rec: st.write("*None*")

st.divider() 

# ==========================================
# PART 2: METHOD COMPARISON TOOL
# ==========================================
st.header("Part 2: Compare Methods")
st.write("Select up to two methods from the recommendations above to compare their specific properties side-by-side.")

all_methods = properties_df['Method'].tolist()

compare_selection = st.multiselect(
    "Select methods to compare (Max 2):",
    options=all_methods,
    max_selections=2
)

if len(compare_selection) > 0:
    if st.button("Compare Methods"):
        compare_df = properties_df[properties_df['Method'].isin(compare_selection)]
        compare_df = compare_df.set_index('Method').T
        st.dataframe(compare_df, use_container_width=True)
