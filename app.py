import streamlit as st
from huggingface_hub import InferenceClient
import base64
from PIL import Image, UnidentifiedImageError
import io
import time

# Load token
HF_TOKEN = st.secrets.get("hf_token")
TEXT_MODEL = "HuggingFaceH4/zephyr-7b-beta"
IMAGE_MODEL = "runwayml/stable-diffusion-v1-5"
client = InferenceClient(TEXT_MODEL, token=HF_TOKEN)
image_client = InferenceClient(IMAGE_MODEL, token=HF_TOKEN)

# Session state to reuse brand identity
if "brand_info" not in st.session_state:
    st.session_state.brand_info = ""

# UI
st.title("🧠 Fake Business Generator")
st.markdown("Create a full fake business identity with AI: branding, logo, and landing page.")
st.markdown("Note: all content is fictional and for educational use only.")

tabs = st.tabs(["🧪 Brand Identity", "🖼️ Logo Generator", "💻 Landing Page"])

def text_to_image_with_retries(prompt, retries=5, delay=5):
    for attempt in range(retries):
        try:
            image_bytes = image_client.text_to_image(
                prompt=prompt,
                guidance_scale=7.5,
                height=512,
                width=512
            )
            
            image = Image.open(io.BytesIO(image_bytes))
            print(image_bytes)

            if isinstance(image, Image.Image):
                return image
            else:
                raise ValueError("Returned object is not a valid image.")
        except (StopIteration, UnidentifiedImageError, ValueError, RuntimeError) as e:
            print(f"[Attempt {attempt + 1}] Image generation failed: {e}")
            time.sleep(delay * (attempt + 1))  # exponential backoff

    st.error("Image generation failed after multiple retries.")

# ────────────────
# 🧪 BRAND IDENTITY
# ────────────────
with tabs[0]:
    st.subheader("Generate a Fake Brand")

    business_type = st.text_input("💼 Business Type", "Luxury coffee subscription")
    tone = st.selectbox("🎨 Brand Tone", ["Luxury", "Playful", "Eco-conscious", "Minimalist", "Edgy"])
    audience = st.text_input("🎯 Target Audience", "Millennial professionals")

    if st.button("🔮 Generate Brand Identity"):
        with st.spinner("Thinking like a brand guru..."):

            messages = [
                {"role": "system", "content": "You are a creative branding strategist AI."},
                {"role": "user", "content": f"""
Create a fake business identity:

- Industry: {business_type}
- Tone: {tone}
- Target Audience: {audience}

Include markdown sections for:
### Brand Name
### Tagline
### About Us
### Founder Bio
### Products (3, each with name + description)
### Customer Reviews (3 short fictional reviews)
"""}
            ]

            try:
                response = client.chat_completion(
                    messages=messages,
                    max_tokens=800,
                    temperature=0.9,
                    top_p=0.95,
                )
                output = response.choices[0].message.content.strip()
                st.session_state.brand_info = output
                st.markdown(output)
            except Exception as e:
                st.error("Failed to generate brand identity.")
                st.exception(e)

# ─────────────
# 🖼️ LOGO
# ─────────────

with tabs[1]:
    st.subheader("Generate a Fake Logo")

    if st.session_state.brand_info:
        brand_lines = st.session_state.brand_info.splitlines()
        brand_name = next(
            (line.split(":", 1)[1].strip() for line in brand_lines if line.lower().startswith("brand name:")),
            "Brand"
        )
        logo_prompt = f"Minimalist modern logo for a {tone.lower()} brand named '{brand_name}' in the {business_type.lower()} industry."

        if st.button("🎨 Generate Logo"):
            with st.spinner("Generating image..."):

                image_returned = text_to_image_with_retries(
                    prompt=logo_prompt
                )
            
                st.image(image_returned, caption=f"Logo for {brand_name}")
    else:
        st.info("Please generate a brand identity first in the first tab.")

# ─────────────────────
# 💻 LANDING PAGE HTML
# ─────────────────────
with tabs[2]:
    st.subheader("Generate a Fake Landing Page")

    if st.session_state.brand_info:
        if st.button("🧱 Generate HTML + CSS"):
            with st.spinner("Coding like a frontend dev..."):

                messages = [
                    {"role": "system", "content": "You are an expert web designer."},
                    {"role": "user", "content": f"""
Create an HTML + CSS landing page based on this fake brand:

{st.session_state.brand_info}

The page should include:
- Brand name & tagline
- Product section
- About/founder blurb
- Fake testimonials

Use clean, modern styling. Return only HTML with embedded CSS.
"""}
                ]

                try:
                    html_response = client.chat_completion(
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.85,
                    )
                    html_code = html_response.choices[0].message.content.strip()
                    st.code(html_code, language="html")

                    b64 = base64.b64encode(html_code.encode()).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="fake_business.html">⬇️ Download HTML</a>'
                    st.markdown(href, unsafe_allow_html=True)

                except Exception as e:
                    st.error("Failed to generate landing page.")
                    st.exception(e)
    else:
        st.info("Please generate a brand identity first in the first tab.")
