import streamlit as st
import os
import io
import json
import re
import time
from datetime import datetime
from pypdf import PdfReader
from PIL import Image
from groq import Groq


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Health Companion",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# GROQ CONFIGURATION
# =========================================================

try:
    API_KEY = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    API_KEY = ""

API_KEY = API_KEY or os.getenv("GROQ_API_KEY", "")
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def ask_grok(system_prompt, user_prompt, max_tokens=1200):
    """Generate a response using Groq's chat-completions API."""
    if not API_KEY:
        raise ValueError("Service configuration is unavailable. Please try again later or contact the app administrator.")

    client = Groq(api_key=API_KEY)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_completion_tokens=max_tokens,
            temperature=0.2,
        )
    except Exception as error:
        error_text = str(error).lower()
        if "401" in error_text or "authentication" in error_text or "invalid api key" in error_text:
            raise RuntimeError("The service could not be reached. Please try again later.") from error
        if "429" in error_text or "rate limit" in error_text or "quota" in error_text:
            raise RuntimeError("The service is busy right now. Please wait a moment and try again.") from error
        raise RuntimeError("The service could not complete your request. Please try again later.") from error

    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("Groq returned an empty response. Please try again.")
    return content.strip()


# =========================================================
# SESSION STATE
# =========================================================

if "records" not in st.session_state:
    st.session_state.records = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "language" not in st.session_state:
    st.session_state.language = "English"

if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #f5f7fb;
    }

    [data-testid="stSidebar"] {
        background: #101c35;
    }

    [data-testid="stSidebar"] * {
        color: #f1f5ff;
    }

    .hero {
        background: linear-gradient(120deg, #123047 0%, #176B67 58%, #2B8A83 100%);
        padding: 34px;
        border-radius: 22px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 12px 32px rgba(18, 48, 71, 0.12);
    }
    .hero h1 { color: white; font-size: 32px; font-weight: 800; margin-bottom: 8px; }
    .hero p { color: #E0F2F1; font-size: 15px; margin-bottom: 0; line-height: 1.65; }
    .metric-card {
        background: white; border: 1px solid #E3EAEF; border-radius: 16px;
        padding: 20px; min-height: 125px; box-shadow: 0 4px 14px rgba(25, 50, 70, 0.035);
    }
    .metric-label { color: #607080; font-size: 13px; font-weight: 600; }
    .metric-value { color: #123047; font-size: 29px; font-weight: 800; margin-top: 9px; }
    .metric-note { color: #718096; font-size: 12px; margin-top: 5px; }
    .section-card {
        background: white; padding: 22px; border-radius: 16px;
        border: 1px solid #E3EAEF; margin-bottom: 16px;
    }
    .action-card {
        background: white; border: 1px solid #E3EAEF; border-radius: 18px;
        padding: 20px 20px 14px 20px; min-height: 170px;
        box-shadow: 0 5px 18px rgba(25, 50, 70, 0.04);
    }
    .action-icon {
        display: inline-block; background: #E8F5F2; color: #176B67;
        padding: 10px 12px; border-radius: 12px; font-size: 22px; margin-bottom: 10px;
    }
    div.stButton > button {
        border-radius: 10px; font-weight: 650; min-height: 44px;
        border: 1px solid #D9E4E8; transition: all 0.15s ease;
    }
    div.stButton > button[kind="primary"] {
        background: #176B67; border-color: #176B67; color: white;
    }
    div.stButton > button:hover { border-color: #176B67; color: #176B67; }
    [data-testid="stFileUploader"] {
        background: white; border: 1px dashed #B8CBCF; border-radius: 14px; padding: 12px;
    }
    [data-testid="stSidebar"] { background: #123047; }
    [data-testid="stSidebar"] * { color: #F3F8FA; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding: 5px 0; }
    h1, h2, h3 { letter-spacing: -0.025em; }
    .stApp { background: #F5F8FA; }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# TRANSLATIONS
# =========================================================

TRANSLATIONS = {
    "English": {
        "overview": "Home",
        "documents": "My Health Records",
        "timeline": "Health History",
        "copilot": "Health Assistant",
        "export": "Download Records",
        "welcome": "Your health information, all in one place.",
        "subtitle": (
            "Keep your reports organized, understand your results, "
            "and find helpful answers to your health questions."
        ),
        "upload": "Add your medical records",
        "analyze": "Review report",
    },
    "Telugu": {
        "overview": "ముఖ్య సమాచారం",
        "documents": "వైద్య పత్రాలు",
        "timeline": "ఆరోగ్య చరిత్ర",
        "copilot": "AI సహాయకుడు",
        "export": "డేటా ఎగుమతి",
        "welcome": "మీ ఆరోగ్య సమాచారాన్ని ఒకే చోట ఉంచండి.",
        "subtitle": (
            "మీ వైద్య నివేదికలను సులభంగా అర్థం చేసుకోండి, "
            "మీ ఆరోగ్య సమాచారాన్ని క్రమబద్ధంగా ఉంచండి."
        ),
        "upload": "వైద్య నివేదికలను జోడించండి",
        "analyze": "నివేదికను చూడండి",
    },
}


# =========================================================
# DOCUMENT TEXT EXTRACTION
# =========================================================

def extract_pdf_text(file_bytes):
    """Extract text from a text-based PDF."""
    reader = PdfReader(io.BytesIO(file_bytes))

    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages).strip()


def extract_image_text(file_bytes):
    """Extract text from an image using Tesseract OCR."""
    import pytesseract

    image = Image.open(io.BytesIO(file_bytes))
    return pytesseract.image_to_string(image).strip()


def extract_document(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    extension = os.path.splitext(uploaded_file.name)[1].lower()

    if extension == ".pdf":
        return extract_pdf_text(file_bytes)

    if extension in [".png", ".jpg", ".jpeg"]:
        return extract_image_text(file_bytes)

    raise ValueError("Unsupported file type.")


# =========================================================
# JSON PARSING
# =========================================================

def parse_json_response(text):
    """Parse JSON returned by the AI model."""
    cleaned = text.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)

        if match:
            return json.loads(match.group(0))

        raise ValueError("We couldn’t prepare the report summary. Please try again.")


def safe_list(value):
    return value if isinstance(value, list) else []


def safe_text(value, default="Not specified"):
    if value is None or str(value).strip() == "":
        return default
    return str(value)


# =========================================================
# MEDICAL DOCUMENT ANALYSIS
# =========================================================

def analyze_medical_document(document_text, language="English"):

    system_prompt = """
You are a friendly Personal Health Copilot.

Explain medical reports in simple, everyday language.

STRICT RESPONSE RULES:
- Use simple words a non-medical person can understand.
- Keep the summary to a maximum of 3 short bullet points.
- Each bullet should be one or two sentences.
- Avoid long paragraphs and unnecessary medical terminology.
- Explain medical terms briefly when needed.
- Preserve test values, units, and reference ranges when available.
- Include only information supported by the uploaded document.
- Do not invent missing information.
- Do not diagnose diseases or prescribe medicines.
- Do not tell users to start, stop, or change medication.
- Explain that abnormal results need professional interpretation.
- Use short lists for findings, follow-up items, and questions.
- If information is missing, use an empty string or empty list.
- Return only valid JSON without Markdown fences.

Use this exact JSON structure:
{
  "document_type": "",
  "document_date": "",
  "summary": "",
  "key_findings": [],
  "lab_results": [
    {
      "test": "",
      "value": "",
      "unit": "",
      "reference_range": "",
      "reported_status": ""
    }
  ],
  "medications": [
    {
      "name": "",
      "dosage": "",
      "instructions": ""
    }
  ],
  "follow_up": [],
  "questions_for_doctor": [],
  "important_notes": []
}
"""

    user_prompt = f"""
Preferred response language: {language}

Analyze this medical document. Keep the summary and explanations
short, clear, and easy to understand.

DOCUMENT TEXT:
{document_text[:18000]}
"""

    response_text = ask_grok(
        system_prompt,
        user_prompt,
        max_tokens=1200,
    )

    return parse_json_response(response_text)


# =========================================================
# DISPLAY HELPERS
# =========================================================

def metric_card(label, value, note):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_bullet_list(items, empty_message="Nothing to show yet."):
    items = safe_list(items)

    if not items:
        st.caption(empty_message)
        return

    for item in items:
        if isinstance(item, dict):
            st.markdown(f"- {json.dumps(item, ensure_ascii=False)}")
        else:
            st.markdown(f"- {item}")


def display_analysis(record):
    analysis = record.get("analysis", {})

    st.markdown("### Quick summary")
    summary = safe_text(
        analysis.get("summary"),
        "No summary was generated.",
    )

    # The AI is instructed to return bullet points in this field.
    st.markdown(summary.replace("\n", "  \n"))

    st.markdown("### Key findings")
    display_bullet_list(
        analysis.get("key_findings"),
        "No key findings were extracted.",
    )

    st.markdown("### Lab results")

    lab_results = [
        item
        for item in safe_list(analysis.get("lab_results"))
        if isinstance(item, dict)
    ]

    if lab_results:
        st.dataframe(
            [
                {
                    "Test": item.get("test", ""),
                    "Value": item.get("value", ""),
                    "Unit": item.get("unit", ""),
                    "Reference range": item.get(
                        "reference_range", ""
                    ),
                    "Reported status": item.get(
                        "reported_status", ""
                    ),
                }
                for item in lab_results
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No lab results were extracted.")

    st.markdown("### Medications mentioned")

    medications = [
        item
        for item in safe_list(analysis.get("medications"))
        if isinstance(item, dict)
    ]

    if medications:
        for med in medications:
            st.markdown(
                f"**{safe_text(med.get('name'))}**"
            )
            st.markdown(
                f"- Dosage: {safe_text(med.get('dosage'))}"
            )
            st.markdown(
                f"- Instructions: "
                f"{safe_text(med.get('instructions'))}"
            )
    else:
        st.caption("No medication entries were extracted.")

    st.markdown("### Follow-up suggestions")
    display_bullet_list(
        analysis.get("follow_up"),
        "No follow-up suggestions were extracted.",
    )

    st.markdown("### Questions to ask your doctor")
    display_bullet_list(
        analysis.get("questions_for_doctor"),
        "No questions were extracted.",
    )

    notes = safe_list(analysis.get("important_notes"))

    if notes:
        st.markdown("### Important notes")
        for note in notes:
            st.warning(str(note))


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## 🩺 Health Companion")
    st.caption("Your health, in one place")
    st.divider()

    language = st.selectbox(
        "Language / భాష",
        ["English", "Telugu"],
        index=["English", "Telugu"].index(
            st.session_state.language
        ),
    )

    st.session_state.language = language
    T = TRANSLATIONS[language]

    st.markdown("### Navigation")

    page_options = [
        T["overview"],
        T["documents"],
        T["timeline"],
        T["copilot"],
        T["export"],
    ]

    # Apply dashboard navigation requests BEFORE creating the radio widget.
    # Streamlit does not allow changing a widget's keyed state after it is rendered.
    pending_page = st.session_state.pop("pending_page_nav", None)
    if pending_page in page_options:
        st.session_state.page_nav = pending_page
    if st.session_state.get("page_nav") not in page_options:
        st.session_state.page_nav = T["overview"]

    page = st.radio(
        "Choose a page",
        page_options,
        key="page_nav",
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("### Your records")
    st.caption(
        f"Reports available now: "
        f"{len(st.session_state.records)}"
    )

    st.caption("Records are available during your current visit. Download anything you want to keep.")


# =========================================================
# PAGE 1: OVERVIEW
# =========================================================

if page == T["overview"]:

    st.markdown(
        f"""
        <div class="hero">
            <h1>🩺 {T["welcome"]}</h1>
            <p>{T["subtitle"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_documents = len(st.session_state.records)

    total_findings = sum(
        len(
            safe_list(
                record.get("analysis", {}).get("key_findings")
            )
        )
        for record in st.session_state.records
    )

    total_medications = sum(
        len(
            safe_list(
                record.get("analysis", {}).get("medications")
            )
        )
        for record in st.session_state.records
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card(
            "Documents uploaded",
            total_documents,
            "Reports currently available",
        )

    with c2:
        metric_card(
            "Key findings",
            total_findings,
            "Found in your reports",
        )

    with c3:
        metric_card(
            "Medication entries",
            total_medications,
            "Listed in your reports",
        )

    st.markdown("## What would you like to do?")
    st.caption("Choose what you would like to do.")

    a1, a2, a3 = st.columns(3, gap="medium")

    with a1:
        st.markdown(
            """
            <div class="action-card">
                <div class="action-icon">📄</div>
                <h3>Upload documents</h3>
                <p style="color:#64748b;font-size:14px;">
                    Add lab reports, prescriptions, or other medical records
                    and get a clear, easy-to-read summary.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Upload a report  →", key="home_upload", type="primary", use_container_width=True):
            st.session_state.pending_page_nav = T["documents"]
            st.rerun()

    with a2:
        st.markdown(
            """
            <div class="action-card">
                <div class="action-icon">🗂️</div>
                <h3>Health history</h3>
                <p style="color:#64748b;font-size:14px;">
                    Review your saved-in-this-visit reports, summaries,
                    and key findings.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("View health history  →", key="home_history", use_container_width=True):
            st.session_state.pending_page_nav = T["timeline"]
            st.rerun()

    with a3:
        st.markdown(
            """
            <div class="action-card">
                <div class="action-icon">💬</div>
                <h3>Health assistant</h3>
                <p style="color:#64748b;font-size:14px;">
                    Ask questions about your reports and get clear explanations
                    of medical terms.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Ask the Copilot  →", key="home_copilot", use_container_width=True):
            st.session_state.pending_page_nav = T["copilot"]
            st.rerun()

    st.markdown("## Recent documents")

    if not st.session_state.records:
        st.info(
            "No documents uploaded yet. Select Medical Documents "
            "in the sidebar to upload your first report."
        )
    else:
        for record in reversed(st.session_state.records[-5:]):
            with st.container(border=True):
                st.markdown(f"**{record['filename']}**")
                st.caption(record.get("uploaded_at", ""))
                st.write(
                    record.get("analysis", {}).get(
                        "summary", "No summary available."
                    )
                )


# =========================================================
# PAGE 2: MEDICAL DOCUMENTS
# =========================================================

elif page == T["documents"]:

    st.title("📄 My Health Records")

    st.write(
        "Add a medical report to see a short, easy-to-understand summary."
    )

    uploaded_files = st.file_uploader(
        T["upload"],
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="You can add PDF, PNG, or JPG files.",
    )

    if uploaded_files:
        selected_file = st.selectbox(
            "Choose a document to analyze",
            uploaded_files,
            format_func=lambda file: file.name,
        )

        if st.button(T["analyze"], type="primary"):

            try:
                with st.spinner(
                    "Reading your document... Please wait."
                ):
                    extracted_text = extract_document(selected_file)

                if not extracted_text:
                    st.error("We couldn’t read text from this file. Try a clearer image or a PDF with selectable text.")

                else:
                    with st.expander("View extracted text"):
                        st.text(extracted_text[:10000])

                    with st.spinner("Reviewing your report..."):
                        analysis = analyze_medical_document(
                            extracted_text,
                            st.session_state.language,
                        )

                    record = {
                        "filename": selected_file.name,
                        "uploaded_at": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "document_text": extracted_text,
                        "analysis": analysis,
                    }

                    st.session_state.records.append(record)
                    st.session_state.last_analysis = record

                    st.success("Your report is ready to review.")

            except Exception as e:
                st.error("We couldn’t read or review this report. Please check the file and try again.")

    if st.session_state.last_analysis:
        st.divider()
        st.subheader("Report overview")
        st.caption(
            st.session_state.last_analysis.get("filename", "")
        )
        display_analysis(st.session_state.last_analysis)

    if st.session_state.records:
        st.divider()
        st.subheader("Uploaded records")

        for index, record in enumerate(
            st.session_state.records
        ):
            with st.expander(record["filename"]):
                st.caption(record.get("uploaded_at", ""))
                st.write(
                    record.get("analysis", {}).get(
                        "summary", "No summary available."
                    )
                )

                if st.button(
                    "Delete this record",
                    key=f"delete_record_{index}",
                ):
                    deleted = st.session_state.records.pop(index)

                    if (
                        st.session_state.last_analysis
                        and st.session_state.last_analysis.get("filename")
                        == deleted.get("filename")
                    ):
                        st.session_state.last_analysis = (
                            st.session_state.records[-1]
                            if st.session_state.records
                            else None
                        )

                    st.rerun()


# =========================================================
# PAGE 3: HEALTH TIMELINE
# =========================================================

elif page == T["timeline"]:

    st.title("🗂️ Health History")

    st.write(
        "Review the reports analyzed during your current session."
    )

    if not st.session_state.records:
        st.info(
            "Your timeline is empty. Analyze a medical document "
            "to add your first entry."
        )
    else:
        for record in reversed(st.session_state.records):

            analysis = record.get("analysis", {})

            with st.container(border=True):
                st.markdown(
                    f"### {record.get('filename', 'Medical document')}"
                )

                st.caption(
                    f"Uploaded: {record.get('uploaded_at', 'Unknown')}"
                )

                if analysis.get("document_date"):
                    st.write(
                        "**Date on report:** "
                        f"{analysis['document_date']}"
                    )

                st.markdown(
                    safe_text(
                        analysis.get("summary"),
                        "No summary available.",
                    )
                )

                findings = safe_list(
                    analysis.get("key_findings")
                )

                if findings:
                    st.markdown("**Key findings**")
                    display_bullet_list(findings)


# =========================================================
# PAGE 4: AI COPILOT
# =========================================================

elif page == T["copilot"]:

    st.title("💬 Health Assistant")

    st.write(
        "Ask questions about your reports and get explanations in simple language."
    )

    st.info(
        "This service helps explain health information but cannot diagnose conditions or replace a healthcare professional. For emergencies, seek urgent medical care. Do not use it to decide whether to start, stop, or change medication."
    )

    # Let the user choose which uploaded report(s) should ground the answer.
    available_records = st.session_state.records
    selected_records = []

    if not available_records:
        st.warning(
            "You have not added a report yet. You can still ask a general health question, but the answer will not be based on your personal records."
        )
        record_choice = "General question (no uploaded records)"
    else:
        record_options = ["All uploaded reports"] + [
            f"{record.get('filename', 'Medical report')} — "
            f"{record.get('uploaded_at', 'date unknown')}"
            for record in available_records
        ]
        record_choice = st.selectbox(
            "Use which medical records?",
            record_options,
            help="Choose one report to focus the answer, or use all uploaded reports.",
        )

        if record_choice == "All uploaded reports":
            selected_records = available_records
        else:
            selected_index = record_options.index(record_choice) - 1
            selected_records = [available_records[selected_index]]

    # Include extracted document text as well as its analysis. Keep the
    # context bounded so very large documents do not overwhelm the prompt.
    records_context = []
    for record in selected_records:
        records_context.append({
            "filename": record.get("filename", "Unknown file"),
            "uploaded_at": record.get("uploaded_at", "Unknown date"),
            "analysis": record.get("analysis", {}),
            "extracted_report_text": record.get("document_text", "")[:5000],
        })

    with st.expander("What can I ask?", expanded=False):
        st.markdown(
            "- What does this test name mean?\n"
            "- What value and reference range are shown in my report?\n"
            "- Which results are marked high or low in the report?\n"
            "- What questions could I ask my healthcare professional?\n"
            "- Compare information in my uploaded reports, if the dates and units allow it."
        )

    # Display existing messages.
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask about your report in simple words...")

    if question:
        st.session_state.chat_history.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                system_prompt = """
You are a careful Personal Health Copilot that explains medical records.

GROUNDING RULES:
- When uploaded records are provided, use them as the primary source for
  questions about the user's own results, medications, dates, and history.
- Do not invent or infer values, units, reference ranges, dates, diagnoses,
  medications, or personal facts.
- If the records do not contain the answer, clearly say:
  "I can't find that information in the selected uploaded records."
  You may then offer general educational context, clearly labelled as general.
- When discussing a specific finding, name the source report when possible.
- Distinguish a value explicitly marked high/low/abnormal in the report from
  your own interpretation. Do not label a result abnormal unless the report
  or its provided reference range supports that statement.
- Do not diagnose, prescribe, or advise starting, stopping, or changing medicine.
- Do not claim to have reviewed files that are not in the supplied context.
- For possible emergency symptoms, recommend seeking urgent medical help.

RESPONSE STYLE:
- Respond in the selected language.
- Start by answering the user's actual question.
- Prefer 3-5 short bullet points and plain language.
- Explain medical terms briefly.
- Mention uncertainty and suggest questions for a qualified healthcare
  professional when appropriate.
- Do not repeat the same point unnecessarily.
"""

                user_prompt = f"""
Preferred response language: {st.session_state.language}
Selected record scope: {record_choice}

USER QUESTION:
{question}

SELECTED UPLOADED RECORDS (analysis and extracted text):
{json.dumps(records_context, ensure_ascii=False)[:16000] if records_context else "No uploaded medical records are available in this context."}

RECENT CONVERSATION:
{json.dumps(st.session_state.chat_history[-6:], ensure_ascii=False)[:4000]}

Answer using the grounding and safety rules. If the selected records do not
support an answer about the user's personal health, say so clearly.
"""

                with st.spinner("Preparing your answer..."):
                    answer = ask_grok(
                        system_prompt,
                        user_prompt,
                        max_tokens=700,
                    )

                st.markdown(answer)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as e:
                error_text = str(e)
                if any(code in error_text.upper() for code in ("503", "UNAVAILABLE", "HIGH DEMAND")):
                    error_message = (
                        "The service is busy right now, so I couldn't answer that question. Your chat and reports are still available during this visit. Please try again shortly."
                    )
                else:
                    error_message = "I couldn’t prepare an answer just now. Please try again in a moment."
                st.warning(error_message)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": error_message}
                )

    if st.session_state.chat_history:
        if st.button("Clear chat history"):
            st.session_state.chat_history = []
            st.rerun()


# =========================================================
# PAGE 5: DATA EXPORT
# =========================================================

elif page == T["export"]:

    st.title("📦 Download Records")

    st.write(
        "Download the reports and summaries available during this visit."
    )

    records = st.session_state.records

    if not records:
        st.info(
            "No records are available yet. Analyze a document first."
        )

    else:
        export_data = {
            "application": "Health Companion",
            "exported_at": datetime.now().isoformat(),
            "format_note": "Export of the records and summaries available in this app.",
            "records": records,
        }

        json_content = json.dumps(
            export_data,
            indent=2,
            ensure_ascii=False,
        )

        st.download_button(
            "Download all records as JSON",
            data=json_content,
            file_name="health_copilot_records.json",
            mime="application/json",
            use_container_width=True,
        )

        st.markdown("### Export preview")
        st.json(export_data)

        st.divider()

        st.markdown("### Structured record download")

        st.caption("A structured copy of the information available in your reports.")

        fhir_like = {
            "resourceType": "Bundle",
            "type": "collection",
            "timestamp": datetime.now().isoformat(),
            "entry": [],
        }

        for record in records:
            analysis = record.get("analysis", {})

            fhir_like["entry"].append({
                "resource": {
                    "resourceType": "DocumentReference",
                    "description": record.get("filename", ""),
                    "date": record.get("uploaded_at", ""),
                    "content": {
                        "summary": analysis.get("summary", ""),
                        "key_findings": safe_list(
                            analysis.get("key_findings")
                        ),
                        "lab_results": safe_list(
                            analysis.get("lab_results")
                        ),
                        "medications": safe_list(
                            analysis.get("medications")
                        ),
                    },
                }
            })

        st.download_button(
            "Download FHIR-inspired JSON",
            data=json.dumps(
                fhir_like,
                indent=2,
                ensure_ascii=False,
            ),
            file_name="health_copilot_fhir_inspired.json",
            mime="application/json",
            use_container_width=True,
        )

        st.info("Your records are available during the current visit. Download a copy if you need to keep them. Avoid using a shared device for private health information.")


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Health Companion • Information here is for general guidance. Confirm important medical decisions with a qualified healthcare professional."
)

