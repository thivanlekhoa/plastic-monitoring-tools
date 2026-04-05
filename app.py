import streamlit as st
import pandas as pd

# Set up the page
st.set_page_config(page_title="Framework for Monitoring Plastic Export", layout="wide")

# --- INITIALIZE SESSION STATE ---
# We use session state to remember actions across button clicks
if 'show_recs' not in st.session_state:
    st.session_state.show_recs = False
if 'auto_compare' not in st.session_state:
    st.session_state.auto_compare = False
if 'compare_widget' not in st.session_state:
    st.session_state.compare_widget = []

# --- LOAD DATA ---
# Removed @st.cache_data so the CSVs load fresh every single time
def load_labels_matrix():
    df = pd.read_csv("labels.csv")
    df.rename(columns={df.columns[0]: 'Method'}, inplace=True)
    # Automatically remove hidden spaces
    df['Method'] = df['Method'].astype(str).str.strip() 
    return df

def load_properties():
    df = pd.read_csv("properties_clean.csv")
    # Automatically remove hidden spaces
    df['Method'] = df['Method'].astype(str).str.strip() 
    return df

labels_df = load_labels_matrix()
properties_df = load_properties()

st.title("🌊 Framework for Monitoring Plastic Export from Rivers to the Ocean")

st.write("""
Use this decision-support tool to identify the most suitable monitoring methods based on your project's specific constraints and goals, and learn how to use them.

**How to use this tool:**
* **Part 1:** First, go through the four categories below and select the labels that best fit your needs. This will filter the options and recommend the most appropriate monitoring methods for your project.
* **Part 2:** If you receive multiple recommendations (such as several "Good Fit" methods), you can use the dropdown in Part 2 to select them and compare their specific properties side-by-side.
""")

st.divider()

# ==========================================
# PART 1: RECOMMENDATION ENGINE
# ==========================================
st.header("Part 1: Find Your Methods")
st.write("Please fill out the categories below to filter the available monitoring methods.")

# --- CALLBACK FUNCTIONS ---
def trigger_recs():
    st.session_state.show_recs = True
    st.session_state.auto_compare = False # Reset comparison flag on new search

def clear_selections():
    st.session_state.dn_key = []
    st.session_state.infra_key = []
    st.session_state.temp_key = []
    st.session_state.res_key = []
    st.session_state.show_recs = False
    st.session_state.auto_compare = False
    st.session_state.compare_widget = []

def trigger_comparison(methods_to_compare):
    st.session_state.compare_widget = methods_to_compare
    st.session_state.auto_compare = True

# --- CATEGORY 1: Data Requirements ---
st.subheader("📊 1. Data Requirements")
st.write("""
*Select the specific type of data you need to collect.*

* **Physical Characterization:** Refers to the physical collection of plastic samples to determine weight, measurements, or polymer types.
* **Floating (Surface) Items:** Focuses exclusively on plastics found on the water's surface layer.
* **Submerged Items:** Targets plastics suspended within the water column below the surface.
""")
data_needs_options = [
    "Physical characterization (mass, polymer)", 
    "Floating (surface) items", 
    "Submerged items in water column"
]
data_needs = st.multiselect("Select your Data Requirements:", options=data_needs_options, key="dn_key")

# --- CATEGORY 2: Infrastructure ---
st.subheader("🏗️ 2. Infrastructure")
st.write("""
*Identify the physical structures and vessels you have access to at your monitoring location. This prevents recommending methods that require unavailable platforms.*

* **Bridge:** A safe, fixed walkway spanning the river, suitable for observation or equipment attachment.
* **Open Water:** Areas without existing structures suitable for observation or equipment attachment.
* **Vessel:** Access to a motorized or non-motorized boat.
* **Anchored Station:** Access to a fixed floating platform, such as a pontoon, buoy, or anchored dock.
""")

infra_options = [
    "Bridge (fixed walkway) available", 
    "Open water (No existing infrastructure)", 
    "Vessel (boat) available", 
    "Anchored station available"
]

infrastructure = st.multiselect("Select your available Infrastructure:", options=infra_options, key="infra_key")

# --- Check for Infrastructure Conflict ---
infra_conflict = "Bridge (fixed walkway) available" in infrastructure and "Open water (No existing infrastructure)" in infrastructure

if infra_conflict:
    st.error("⚠️ You cannot select 'Open water' and 'Bridge' at the same time. You can only select one of them, please try again.")

# --- CATEGORY 3: Temporal Scope ---
st.subheader("⏱️ 3. Temporal Scope")
st.write("""
* **Continuous:** Monitoring can run continuously during a certain time interval.
* **Intermittent:** Monitoring will be disrupted or paused to set up facilities, change locations, or reset equipment.
""")
temporal_options = [
    "Continuous", 
    "Intermittent" 
]
temporal = st.multiselect("Select your Temporal Scope:", options=temporal_options, key="temp_key")

# --- CATEGORY 4: Resource Capacity ---
st.subheader("💰 4. Resource Capacity")
st.write("""
Budget encompasses both capital investment and operational costs. Please refer to our documentation for specific budget tier definitions. Selecting a higher budget level will also include recommendations for lower-tier methods (e.g., "High" includes Medium and Low; "Medium" includes Low).
""")
resource_options = [
    "Low budget", 
    "Medium budget", 
    "High budget"
]
resource = st.multiselect("Select your Resource Capacity:", options=resource_options, key="res_key")

# --- ACTION BUTTONS ---
col_btn1, col_btn2 = st.columns([1, 5])

with col_btn1:
    st.button("Get Recommendations", type="primary", disabled=infra_conflict, on_click=trigger_recs)

with col_btn2:
    st.button("Reset Selections", on_click=clear_selections)


# --- RECOMMENDATION LOGIC ---
if st.session_state.show_recs:
    good_fit = []
    possible_fit = []
    not_rec = []
    
    clean_good_fit = []
    clean_possible_fit = []

    # Apply Cascading Logic for Resource Capacity
    effective_resource = list(resource)
    if "High budget" in resource:
        if "Medium budget" not in effective_resource: effective_resource.append("Medium budget")
        if "Low budget" not in effective_resource: effective_resource.append("Low budget")
    elif "Medium budget" in resource:
        if "Low budget" not in effective_resource: effective_resource.append("Low budget")

    # Dictionary to group user selections by category
    selected_categories = {
        "Data Needs": data_needs,
        "Infrastructure": infrastructure,
        "Temporal": temporal,
        "Resource": effective_resource
    }

    # For exclusion flag checks
    all_selected_labels = data_needs + infrastructure + temporal + resource
    has_open_water = any("Open water" in label for label in all_selected_labels)
    has_submerged = any("Submerged items" in label for label in all_selected_labels)
    has_characterization = any("Physical characterization" in label for label in all_selected_labels)

    # Loop through each method in the matrix
    for index, row in labels_df.iterrows():
        method_name = str(row['Method']).strip()
        category_match_count = 0
        exclusion_reasons_list = []
        matched_categories_list = []

        # Score by Category (Max 1 point per category)
        for category, labels_in_category in selected_categories.items():
            category_matched = False
            
            for label in labels_in_category:
                if label in labels_df.columns:
                    cell_value = str(row[label]).strip().lower()
                    if cell_value == 'x':
                        category_matched = True
                        break # Stop checking this category once we find 1 match
            
            if category_matched:
                category_match_count += 1
                matched_categories_list.append(category)

        # --- LOGIC: Apply Exclusion Rules ---
        bridge_methods = ["Visual counting from bridge", "Bridge-mounted camera sensor", "Surface trawling from bridge", "Net trawling from bridge"]
        if has_open_water and any(m in method_name for m in bridge_methods):
            exclusion_reasons_list.append("Requires Bridge")

        visual_methods = ["Visual counting from bridge", "Visual counting from boat"]
        if has_submerged and any(m in method_name for m in visual_methods):
            exclusion_reasons_list.append("Cannot see submerged items")

        characterization_methods = ["Visual counting from bridge", "Bridge-mounted camera sensor", "Visual counting from boat"]
        if has_characterization and any(m in method_name for m in characterization_methods):
            exclusion_reasons_list.append("Cannot physically characterize mass/polymer")

        # --- LOGIC: Sort into Buckets ---
        if len(exclusion_reasons_list) > 0:
            exclude_reason_text = "(" + " & ".join(exclusion_reasons_list) + ")"
            not_rec.append(f"**{method_name}**\n\n*{exclude_reason_text}*")
        else:
            if len(matched_categories_list) > 0:
                match_text = "(Matches: " + ", ".join(matched_categories_list) + ")"
            else:
                match_text = "(No exact matches, but not excluded)"

            if category_match_count >= 3:
                good_fit.append(f"**{method_name}**\n\n*{match_text}*")
                clean_good_fit.append(method_name) 
            elif category_match_count >= 1:
                possible_fit.append(f"**{method_name}**\n\n*{match_text}*")
                clean_possible_fit.append(method_name) 

    # Display the sorted buckets neatly
    st.markdown("### 🏆 Your Recommendations")
    
    if len(all_selected_labels) == 0:
        st.warning("Please select at least one filter above to see recommendations.")
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("✅ **Good Fit**\n\n(Matches in 3-4 categories)")
            for m in good_fit: st.success(m)
            if not good_fit: st.write("*None*")
        with col2:
            st.warning("⚠️ **Possible Fit**\n\n(Matches in 1-2 categories)")
            for m in possible_fit: st.warning(m)
            if not possible_fit: st.write("*None*")
        with col3:
            st.error("❌ **NOT RECOMMENDED**\n\n(Rule Exclusions)")
            for m in not_rec: st.error(m)
            if not not_rec: st.write("*None*")

        # --- AUTO COMPARE BUTTON LOGIC ---
        methods_to_compare = []

        if len(clean_good_fit) > 1:
            methods_to_compare = clean_good_fit
        elif len(clean_good_fit) == 1:
            if len(clean_possible_fit) > 0:
                methods_to_compare = clean_good_fit + clean_possible_fit
        elif len(clean_good_fit) == 0:
            if len(clean_possible_fit) > 1:
                methods_to_compare = clean_possible_fit

        if len(methods_to_compare) > 1:
            st.write("") 
            st.button(
                "📊 Compare Recommended Methods", 
                type="secondary", 
                on_click=trigger_comparison, 
                args=(methods_to_compare,)
            )

st.divider() 

# ==========================================
# PART 2: METHOD COMPARISON TOOL
# ==========================================
st.header("Part 2: Compare Methods")
st.write("Select methods to compare their specific properties side-by-side.")

all_methods = properties_df['Method'].tolist()

compare_selection = st.multiselect(
    "Select methods to compare:",
    options=all_methods,
    key="compare_widget" 
)

if len(compare_selection) > 0:
    if st.button("Compare Methods") or st.session_state.auto_compare:
        st.session_state.auto_compare = False 
        
        compare_df = properties_df[properties_df['Method'].isin(compare_selection)]
        compare_df = compare_df.set_index('Method').T
        st.dataframe(compare_df, use_container_width=True, height=800)
