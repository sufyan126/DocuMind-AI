import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import google.generativeai as genai
from dotenv import load_dotenv
import os
from database import init_db, signup, login, save_message, get_history, clear_history
from google.api_core.exceptions import ResourceExhausted, InvalidArgument
from fpdf import FPDF

thanks_words = ["thank you", "thanks", "thankyou", "thx", "shukriya"]

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", None)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="DocuMind AI", page_icon="🧠", layout="wide")

init_db()

def export_chat_to_pdf(chat_history):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "DocuMind AI Chat History", ln=True, align="C")
    pdf.ln(10)

    for role, message in chat_history:
        role_title = "User" if role == "user" else "AI"
        pdf.set_font("Arial", style="B", size=12)
        pdf.multi_cell(0, 8, f"{role_title}:")
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 8, str(message).encode("latin-1", "replace").decode("latin-1"))
        pdf.ln(5)

    file_path = "chat_history.pdf"
    pdf.output(file_path)
    return file_path


def safe_generate(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text

    except ResourceExhausted:
        return "Gemini free limit reached. Please try again later."

    except InvalidArgument:
        return "AI request too large. Please ask a shorter question or use a smaller PDF."

    except Exception as e:
        return "AI response failed. Please try again later."


# ---------------- LOGIN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_gmail" not in st.session_state:
    st.session_state.user_gmail = ""

if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .login-title {
        color: white;
        font-size: 34px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 8px;
    }
    .login-subtitle {
        color: #9CA3AF;
        font-size: 15px;
        text-align: center;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=140)
        elif os.path.exists("logo.png"):
            st.image("logo.png", width=140)

        st.markdown("""
        <div class="login-title">Welcome to DocuMind AI</div>
        <div class="login-subtitle">Login or create an account to continue</div>
        """, unsafe_allow_html=True)

        option = st.radio(
            "Choose option",
            ["Login", "Signup"],
            horizontal=True,
            label_visibility="collapsed"
        )

        gmail = st.text_input("Gmail", placeholder="Enter your Gmail")
        password = st.text_input("Password", placeholder="Enter your password", type="password")

        if option == "Signup":
            if st.button("Create Account", use_container_width=True):
                if not gmail or not password:
                    st.error("Please enter Gmail and password.")
                elif not gmail.endswith("@gmail.com"):
                    st.error("Please enter a valid Gmail address.")
                else:
                    if signup(gmail, password):
                        st.success("Account created successfully. Please login.")
                    else:
                        st.error("This Gmail already exists.")

        if option == "Login":
            if st.button("Login", use_container_width=True):
                if login(gmail, password):
                    st.session_state.logged_in = True
                    st.session_state.user_gmail = gmail
                    st.session_state.chat_history = get_history(gmail)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid Gmail or password.")

    st.stop()


# ---------------- CSS ----------------
st.markdown("""
<style>
.feature-card {
    background: #222222;
    padding: 22px;
    border-radius: 20px;
    text-align: center;
    border: 1px solid #444;
    color: white;
    box-shadow: 0 4px 14px rgba(0,0,0,0.18);
    transition: all 0.3s ease;
    min-height: 135px;
}
.feature-card:hover {
    transform: translateY(-6px);
    border-color: #AAAAAA;
    box-shadow: 0 10px 25px rgba(0,0,0,0.28);
}
.feature-icon {
    font-size: 34px;
}
.feature-title {
    font-size: 21px;
    font-weight: bold;
    margin-top: 10px;
    color: #FFFFFF;
}
.feature-text {
    color: #D1D5DB;
    font-size: 15px;
    margin-top: 6px;
}
.footer {
    text-align: center;
    color: gray;
    font-size: 14px;
    margin-top: 40px;
}
.hero-box {
    background: linear-gradient(135deg, #111111, #2F2F2F);
    padding: 35px 45px;
    border-radius: 28px;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.30);
}
.hero-title {
    color: white;
    font-size: 60px;
    font-weight: 800;
    margin-bottom: 10px;
}
.hero-subtitle {
    color: #D1D5DB;
    font-size: 22px;
    margin-bottom: 10px;
}
.hero-text {
    color: #9CA3AF;
    font-size: 17px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)


# ---------------- HEADER ----------------
logo_path = "assets/logo.png" if os.path.exists("assets/logo.png") else "logo.png"

st.markdown('<div class="hero-box">', unsafe_allow_html=True)

col1, col2 = st.columns([2.3, 5])

with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=240)

with col2:
    st.markdown("""
    <div class="hero-title">DocuMind AI</div>
    <div class="hero-subtitle">AI-powered OCR PDF Study Assistant</div>
    <div class="hero-text">
        Upload scanned PDFs, ask questions, generate summaries, and create exam questions.
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


# ---------------- FEATURE CARDS ----------------
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📄</div>
        <div class="feature-title">OCR Reader</div>
        <div class="feature-text">Extract text from scanned PDFs.</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">💬</div>
        <div class="feature-title">PDF Chatbot</div>
        <div class="feature-text">Ask questions from your uploaded notes.</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📝</div>
        <div class="feature-title">Exam Helper</div>
        <div class="feature-text">Generate summaries and important questions.</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = get_history(st.session_state.user_gmail)


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.write(f"👤 Logged in as: {st.session_state.user_gmail}")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_gmail = ""
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")

    st.header("📂 Upload Document")
    uploaded_files = st.file_uploader(
        "Choose scanned PDF files",
        type="pdf",
        accept_multiple_files=True
    )

    st.markdown("---")

    if st.button("📥 Export Chat to PDF"):
        if st.session_state.chat_history:
            pdf_path = export_chat_to_pdf(st.session_state.chat_history)

            with open(pdf_path, "rb") as file:
                st.download_button(
                    label="Download Chat PDF",
                    data=file,
                    file_name="DocuMind_Chat_History.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("No chat history to export.")

    st.markdown("---")

    if st.button("🧹 Clear Chat"):
        clear_history(st.session_state.user_gmail)
        st.session_state.chat_history = []
        st.success("Chat cleared!")


# ---------------- PDF PROCESSING ----------------
if uploaded_files:
    full_text = ""
    total_pages = 0

    st.success(f"✅ {len(uploaded_files)} PDF file(s) uploaded successfully!")

    with st.spinner("📖 Reading PDFs and extracting text using OCR..."):
        for uploaded_file in uploaded_files:
            if os.name == "nt":
                images = convert_from_bytes(
                    uploaded_file.read(),
                    poppler_path=r"C:\Release-24.08.0-0\poppler-24.08.0\Library\bin"
                )
            else:
                images = convert_from_bytes(uploaded_file.read())

            total_pages += len(images)

            for img in images:
                page_text = pytesseract.image_to_string(img)
                full_text += page_text + "\n"

        st.session_state.pdf_text = full_text

    st.info(f"📄 Total Pages: {total_pages} | 🔤 Characters Extracted: {len(full_text)}")


# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📌 Summary / Notes", "📝 Questions"])


with tab1:
    st.markdown("### 🔍 Search in PDF")

    search_query = st.text_input("Search any keyword from PDF")

    if search_query:
        matched_lines = [
            line for line in st.session_state.pdf_text.split("\n")
            if search_query.lower() in line.lower()
        ]

        if matched_lines:
            st.success(f"Found {len(matched_lines)} matching results")
            for result in matched_lines[:20]:
                st.markdown(f"""
                <div style="
                background:#222;
                padding:12px;
                border-radius:10px;
                margin-bottom:10px;
                border-left:4px solid #888;
                color:white;
                ">
                {result}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No matching results found.")

    st.markdown("### 💬 Chat with your PDF")

    for role, message in st.session_state.chat_history:
        if message and str(message).strip() and str(message) != "None":
            with st.chat_message(role):
                st.write(message)

    question = st.chat_input("Ask a question from PDF")

    if question and question.strip():
        if not st.session_state.pdf_text.strip():
            st.warning("Please upload a PDF first.")
        else:
            if any(word in question.lower() for word in thanks_words):
                answer = "You're welcome! 😊 I'm happy to help you."
            else:
                pdf_context = st.session_state.pdf_text[:1500]

                prompt = f"""
You are an intelligent AI study assistant.

Answer the student question using the PDF context if available.
If the answer is not in the PDF context, use your own AI knowledge.

Rules:
- Use simple student-friendly language.
- If user asks for 2 marks, give a short answer.
- If user asks for 5 marks, give definition, explanation, and key points.
- If user asks for 10 marks, give definition, detailed explanation, example, advantages, limitations, and conclusion.

PDF Context:
{pdf_context}

Question:
{question}
"""

                with st.spinner("🤖 AI is thinking..."):
                    answer = safe_generate(prompt)

            st.session_state.chat_history.append(("user", question))
            st.session_state.chat_history.append(("assistant", answer))

            save_message(st.session_state.user_gmail, "user", question)
            save_message(st.session_state.user_gmail, "assistant", answer)

            st.rerun()


with tab2:
    st.markdown("### 📌 PDF Summary")

    if st.button("Generate Summary", use_container_width=True):
        if not st.session_state.pdf_text.strip():
            st.warning("Please upload a PDF first.")
        else:
            pdf_context = st.session_state.pdf_text[:1500]

            summary_prompt = f"""
Summarize the document below in simple student-friendly language.
Use headings and bullet points.

Context:
{pdf_context}
"""

            with st.spinner("📌 Generating summary..."):
                summary_answer = safe_generate(summary_prompt)

            st.write(summary_answer)

    st.markdown("### 📘 AI Notes")

    if st.button("📘 Generate AI Notes", use_container_width=True):
        if not st.session_state.pdf_text.strip():
            st.warning("Please upload a PDF first.")
        else:
            pdf_context = st.session_state.pdf_text[:1500]

            notes_prompt = f"""
Create clean and well-structured study notes from the document below.

Rules:
- Use simple language.
- Use headings and bullet points.
- Highlight important concepts.
- Include definitions where needed.

Document:
{pdf_context}
"""

            with st.spinner("🧠 Creating smart study notes..."):
                notes_answer = safe_generate(notes_prompt)

            st.write(notes_answer)


with tab3:
    st.markdown("### 📝 Important Questions")

    if st.button("Generate Important Questions", use_container_width=True):
        if not st.session_state.pdf_text.strip():
            st.warning("Please upload a PDF first.")
        else:
            pdf_context = st.session_state.pdf_text[:1500]

            questions_prompt = f"""
From the document below, generate 15 important exam questions.

Write only numbered questions like:
1. Question
2. Question
3. Question

Do not write explanations.

Context:
{pdf_context}
"""

            with st.spinner("📝 Generating important questions..."):
                questions_answer = safe_generate(questions_prompt)

            st.write(questions_answer)


# ---------------- FOOTER ----------------
st.markdown("""
<div class="footer">
    Built with Python, Streamlit, Tesseract OCR, Poppler, and Gemini AI
</div>
""", unsafe_allow_html=True)