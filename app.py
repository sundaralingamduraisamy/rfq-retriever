import streamlit as st
from backend.utils.ingestion import ingest_documents
from backend.utils.retriever import retrieve_similar
from backend.models.generator import generate_rfq

st.set_page_config(page_title="RFQ AI Assistant", layout="centered")
st.title("RFQ AI Chat Assistant 🤖")

ingest_documents()

if "stage" not in st.session_state:
    st.session_state.stage = "start"
    st.session_state.rfq_candidates = []
    st.session_state.selected_context = None

user_input = st.chat_input("Describe what RFQ you need...")

if user_input:

    # Step 1: Get requirement → retrieve RFQs
    if st.session_state.stage == "start":
        st.write("Searching matching RFQs...")
        results = retrieve_similar(user_input)

        st.session_state.rfq_candidates = results
        st.session_state.stage = "select"

        st.subheader("Top 5 Matching RFQs Found")
        for r in results:
            st.write(f"**Option {r['rank']} (Score {r['score']:.2f})**")
            st.write(r["content"][:500] + "...\n")

        st.info("Type: select 1 / select 2 / select 3 / select 4 / select 5")

    # Step 2: User selects RFQ
    elif st.session_state.stage == "select":
        if user_input.lower().startswith("select"):
            try:
                num = int(user_input.split(" ")[1])
                st.session_state.selected_context = st.session_state.rfq_candidates[num - 1]["content"]
                st.session_state.stage = "details"

                st.success("Context selected.")
                st.write("Provide more details like:")
                st.write("- Quantity\n- Budget\n- Delivery timeline\n- Compliance needs\n- Vendor expectations")

            except:
                st.error("Wrong selection format. Use: select 1")

    # Step 3: User answers → Generate RFQ
    elif st.session_state.stage == "details":
        rfq = generate_rfq(user_input, st.session_state.selected_context)
        st.session_state.stage = "done"

        st.subheader("Generated RFQ Draft")
        st.write(rfq)
        st.download_button("Download RFQ", rfq)
