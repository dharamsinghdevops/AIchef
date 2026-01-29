import streamlit as st
import os
import json
import base64
from groq import Groq
import plotly.graph_objects as go

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# IDs for 2026
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct" 
RECIPE_MODEL = "llama-3.3-70b-versatile"

st.set_page_config(page_title="AI Sous Chef Pro", page_icon="🍳", layout="wide")

# Enhanced Styling
st.markdown("""
    <style>
    .ingredient-card { background-color: #1e2130; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 6px solid #00CC96; }
    .step-card { background-color: #262730; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #3e4259; }
    </style>
""", unsafe_allow_html=True)

st.title("🍳 AI Sous Chef Pro")

with st.sidebar:
    st.header("👤 Your Profile")
    goal = st.selectbox("Health Goal", ["Muscle Gain", "Weight Loss", "General Health"])
    diet = st.multiselect("Dietary Preferences", ["Vegan", "Keto", "Gluten-Free", "Low Carb"])

# --- STEP 1: DUAL INPUT ---
st.subheader("📸 Step 1: Capture Ingredients")
col_a, col_b = st.columns([1, 1.2])

if 'detected_items' not in st.session_state:
    st.session_state.detected_items = []

with col_a:
    # Offering both Camera and Upload for maximum reliability
    input_mode = st.radio("Choose Input Type:", ["Live Camera", "Upload Photo"], horizontal=True)
    
    img_file = None
    if input_mode == "Live Camera":
        img_file = st.camera_input("Point at your ingredients")
    else:
        img_file = st.file_uploader("Choose a photo", type=["jpg", "png", "jpeg"])
    
    if img_file and st.button("🔍 AI Analyze Photo", use_container_width=True):
        base64_image = base64.b64encode(img_file.getvalue()).decode('utf-8')
        try:
            vision_res = client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "List the food items/ingredients. Names only, comma separated."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                model=VISION_MODEL, 
            )
            raw_items = vision_res.choices[0].message.content
            st.session_state.detected_items = [i.strip() for i in raw_items.split(',')]
            st.rerun()
        except Exception as e:
            st.error(f"Vision Error: {e}")

with col_b:
    st.write("### 🏷️ AI Labeling")
    manual_input = st.text_area(
        "Refine ingredients (e.g. Change Chicken to Mutton):", 
        value=", ".join(st.session_state.detected_items),
        height=120
    )
    if st.session_state.detected_items:
        st.pills("Recognized Tags:", st.session_state.detected_items, selection_mode="single", disabled=True)

# --- STEP 2: RECIPE GENERATION ---
st.markdown("---")
if st.button("🚀 Generate Personalized Recipe", use_container_width=True):
    with st.spinner("👨‍🍳 Master Chef is calculating..."):
        try:
            # Force clean structure
            prompt = f"""Using {manual_input}, create a healthy {goal} recipe ({diet}).
            Protein source must match user input. 
            Return ONLY JSON: 
            {{
                "recipe_name": "string",
                "calories": "int",
                "protein_grams": "int",
                "fat_grams": "int",
                "carb_grams": "int",
                "prep_time_mins": "int",
                "ingredients": ["Item Name and Quantity"],
                "steps": ["Step Detail"],
                "health_score": "int"
            }}"""
            
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=RECIPE_MODEL,
                response_format={"type": "json_object"}
            )
            recipe = json.loads(response.choices[0].message.content)

            # Dashboard Header
            st.header(f"🍴 {recipe.get('recipe_name')}")
            score = recipe.get('health_score', 80)
            st.write(f"**Goal Match:** {score}/100")
            st.progress(score / 100)

            m_col1, m_col2 = st.columns([1, 1.5])
            with m_col1:
                st.metric("Calories", f"{recipe.get('calories')} kcal")
                st.metric("Prep Time", f"{recipe.get('prep_time_mins')} min")
                st.metric("Protein", f"{recipe.get('protein_grams')}g")
            
            with m_col2:
                # Macros Donut Chart
                fig = go.Figure(data=[go.Pie(
                    labels=['Protein', 'Fats', 'Carbs'], 
                    values=[recipe.get('protein_grams', 0), recipe.get('fat_grams', 0), recipe.get('carb_grams', 0)], 
                    hole=.5,
                    marker=dict(colors=['#00CC96', '#EF553B', '#636EFA'])
                )])
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig, use_container_width=True)

            st.divider()
            c_left, c_right = st.columns(2)
            with c_left:
                st.subheader("🛒 Ingredients List")
                for item in recipe.get('ingredients', []):
                    st.markdown(f'<div class="ingredient-card">✅ {item}</div>', unsafe_allow_html=True)
            
            with c_right:
                st.subheader("👨‍🍳 Instructions")
                for i, step in enumerate(recipe.get('steps', [])):
                    st.markdown(f'<div class="step-card"><b>Step {i+1}:</b> {step}</div>', unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"Recipe Error: {e}")