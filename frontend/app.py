import streamlit as st
import requests
API_BASE = "http://127.0.0.1:8000"
st.set_page_config(page_title="FactoryMind AI", layout="wide")
page = st.sidebar.radio(
    "Navigation",
    ["Ask Assistant", "Incident Explorer", "Add Incident", "Import Incidents", "About"]
)
if page == "Ask Assistant":
    st.title("FactoryMind AI")
    st.subheader("Industrial AI Troubleshooting Assistant")
    st.info(
    "Describe a machine issue and the system will retrieve similar past incidents "
    "and generate an AI-based diagnosis."
    )
    st.write("This web app allows users to ask machine troubleshooting questions, "
        "explore past incidents, and receive AI-generated insights."
    )

    st.divider()
    query = st.text_area(
    "Describe the machine problem",
    placeholder="Example: Coolant pressure keeps dropping during operation..."
    )

    ask_clicked = st.button("Ask Assistant")

# 🔹 STEP 1: Handle API call only
    if ask_clicked:
        st.session_state.pop("last_result", None) 
        st.session_state.pop("feedback", None)
        if not query.strip():
            st.warning("Please describe the problem before asking.")
        else:
            with st.spinner("Analyzing..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/ask",
                        json={"query": query}
                    )
                    if response.status_code == 200:
                        st.session_state["last_result"] = response.json()
                        st.session_state["last_query"] = query
                    else:
                        st.error("Error from backend")
                except Exception as e:
                    st.error(f"Connection error: {e}")


# 🔹 STEP 2: Always display result if exists
    if "last_result" in st.session_state:
        data = st.session_state["last_result"]

        st.subheader("AI Diagnosis")
        answer = data["answer"]

        st.markdown(f"**Root Cause:** {answer['root_cause']}")
        st.markdown(f"**Suggested Fix:** {answer['suggested_fix']}")
        st.markdown(f"**Confidence:** {answer['confidence']}")

        st.divider()
        st.subheader("Was this helpful?")

        if "feedback" not in st.session_state:
            st.session_state.feedback = None

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Helpful"):
                response = requests.post(
                    f"{API_BASE}/feedback",
                    json={
                        "query": st.session_state["last_query"],
                        "answer": answer["suggested_fix"],
                        "is_helpful": True,
                    }
                )
                if response.status_code == 200:
                    st.session_state.feedback = "helpful"

        with col2:
            if st.button("Not Helpful"):
                response = requests.post(
                    f"{API_BASE}/feedback",
                    json={
                        "query": st.session_state["last_query"],
                        "answer": answer["suggested_fix"],
                        "is_helpful": False,
                    }
                )
                if response.status_code == 200:
                    st.session_state.feedback = "not_helpful"

        if st.session_state.feedback == "helpful":
            st.success("Thanks! This will help improve the system.")
        elif st.session_state.feedback == "not_helpful":
            st.warning("Got it. We’ll use this to improve results.")

        st.subheader("Similar Incidents")

        for i, incident in enumerate(data["similar_incidents"], start=1):
            with st.expander(
                f"Incident {i} — {incident['machine_id']} | {incident['category']} | {incident['severity']}"
            ):
                st.write(f"**Description:** {incident['description']}")
                st.write(f"**Resolution:** {incident['resolution']}")
                st.write(f"**Timestamp:** {incident['timestamp']}")

if page == "Incident Explorer":
    st.title("Incident Explorer")
    st.write("Browse historical incidents stored in the system.")

    severity_filter = st.selectbox(
        "Filter by severity",
        ["All", "High", "Medium", "Low"]
    )

    try:
        params = {}
        if severity_filter != "All":
            params["severity"] = severity_filter

        response = requests.get(f"{API_BASE}/incidents", params=params)

        if response.status_code == 200:
            incidents = response.json()
            st.write(f"Total incidents: {len(incidents)}")

            for i, incident in enumerate(incidents, start=1):
                with st.expander(
                    f"Incident {i} — {incident['machine_id']} | {incident['category']} | {incident['severity']}"
                ):
                    st.write(f"**Description:** {incident['description']}")
                    st.write(f"**Resolution:** {incident['resolution']}")
                    st.write(f"**Timestamp:** {incident['timestamp']}")
        else:
            st.error("Could not load incidents from backend.")

    except Exception as e:
        st.error(f"Connection error: {e}")

if page == "Add Incident":
    st.title("Add New Incident")

    machine_id = st.text_input("Machine ID")
    category = st.text_input("Category")
    severity = st.selectbox("Severity", ["Low", "Medium", "High"])
    description = st.text_area("Problem Description")
    resolution = st.text_area("Resolution")

    submit = st.button("Submit Incident")
    if submit:
        payload = {
            "machine_id": machine_id,
            "category": category,
            "severity": severity,
            "description": description,
            "resolution": resolution,
        }

        try:
            response = requests.post(
                f"{API_BASE}/incidents",
                json=payload
            )

            if response.status_code == 200:
                st.success("Incident added successfully.")
            else:
                st.error("Failed to add incident.")

        except Exception as e:
            st.error(f"Connection error: {e}")
if page == "About":
    st.title("About FactoryMind")

    st.write(
        "FactoryMind is an AI-powered industrial troubleshooting assistant. "
        "It helps analyze machine issues by retrieving similar past incidents "
        "and generating explanations using AI."
    )

    st.subheader("How it works")

    st.markdown("""
    - User submits a problem description  
    - System generates embeddings using SentenceTransformers  
    - System retrieves similar incidents from PostgreSQL using pgvector  
    - Uses a language model (LLM) to generate an explanation  
    """)

    st.subheader("Tech Stack")

    st.markdown("""
    - FastAPI (backend API)  
    - PostgreSQL (Supabase) + SQLAlchemy  
    - pgvector (vector search)  
    - SentenceTransformers (embeddings)  
    - LLM (reasoning engine)  
    - Streamlit (frontend prototype)  
    """)

if page == "Import Incidents":
    st.title("Import Incidents")
    st.write("Upload a CSV file of historical factory incidents.")

    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv", "xlsx"])

    if uploaded_file is not None:
        if st.button("Import File"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

            try:
                response = requests.post(
                    f"{API_BASE}/incidents/import",
                    files=files
                )

                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Imported {data['imported']} incidents successfully.")
                    st.write(f"Skipped duplicates: {data['skipped_duplicates']}")
                    st.write(f"Skipped invalid rows: {data['skipped_invalid']}")
                    st.write(f"Batch ID: {data['batch_id']}")
                else:
                    st.error(f"Import failed: {response.text}")

            except Exception as e:
                st.error(f"Connection error: {e}")    