import { useState } from "react";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import "./App.css";

const API = "http://127.0.0.1:8000";

function formatRFQContent(text) {
  if (!text) return "";
  return text
    .replace(/(\d+\.\s)/g, "\n\n$1")
    .replace(
      /(REQUEST FOR QUOTATION|RFQ ID|Industry|Background & Objective|Scope of Work|Technical Requirements|Service Level Agreement|Compliance & Standards|Commercial Terms|Delivery Timeline|Evaluation Criteria)/gi,
      "\n\n$1"
    )
    .trim();
}

export default function App() {
  const [input, setInput] = useState("");
  const [chat, setChat] = useState([
    {
      role: "agent",
      text:
        "Hello. I’m ready to help you draft a new Request for Quotation. Please provide your requirements."
    }
  ]);

  const [history, setHistory] = useState([]);
  const [selectedRFQ, setSelectedRFQ] = useState(null);
  const [editorText, setEditorText] = useState("");

  // PDF Popup
  const [pdfURL, setPdfURL] = useState("");
  const [showPDF, setShowPDF] = useState(false);

  // -----------------------------
  // EXPORT PDF or DOC
  // -----------------------------
  async function exportRFQ(format) {
    if (!editorText.trim()) return;

    const res = await fetch(`${API}/export/${format}`, {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: editorText
    });

    const data = await res.json();

    if (data.path) window.open(`${API}/${data.path}`, "_blank");
  }

  // -----------------------------
  // SEND MESSAGE
  // -----------------------------
  async function sendMessage() {
    if (!input.trim()) return;

    setChat(c => [...c, { role: "user", text: input }]);

    const res = await fetch(`${API}/search_rfq`, 
 {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_intent: input })
    });

    const data = await res.json();

    // =============== FIXED SECTION =================
    // Now ONLY depends on backend
    // Always show RFQs if backend sends them
    if (data.retrieved_rfqs && data.retrieved_rfqs.length > 0) {
      const normalized = data.retrieved_rfqs.map((r, idx) => ({
        id: r.id || `RFQ_${idx + 1}`,
        title: `${r.id || "RFQ"} (score ${r.score?.toFixed(2) || "--"})`,
        content: r.content || "",
        file: r.file || null
      }));

      setHistory(normalized);
      setSelectedRFQ(null);
      setEditorText("");

      setChat(c => [
        ...c,
        { role: "agent", text: "I found similar RFQs. Select one to view." }
      ]);

      setInput("");
      return;
    }
    // =================================================

    // FINAL RFQ GENERATED
    if (data.final_rfq && data.final_rfq.trim().length >= 30) {
      setHistory([]);
      setSelectedRFQ({
        id: "New RFQ",
        title: "New RFQ Draft",
        content: data.final_rfq
      });

      setEditorText(formatRFQContent(data.final_rfq));

      setChat(c => [
        ...c,
        { role: "agent", text: "Draft RFQ created. You can edit it below." }
      ]);

      setInput("");
      return;
    }

    // CLARIFICATION MODE
    if (data.requires_clarification === true) {
      setHistory([]);
      setSelectedRFQ(null);
      setEditorText("");

      setChat(c => [
        ...c,
        {
          role: "agent",
          text:
            data.clarification_question ||
            "Please provide scope, SLA, compliance, volume, and timeline."
        }
      ]);

      setInput("");
      return;
    }

    // SAFETY NET
    setChat(c => [
      ...c,
      { role: "agent", text: "Please provide more detailed RFQ requirements." }
    ]);

    setInput("");
  }

  // -----------------------------
  // SELECT RFQ
  // -----------------------------
  function selectRFQ(rfq) {
    setSelectedRFQ(rfq);

    if (rfq.file) {
      setPdfURL(`http://127.0.0.1:8000/rfq_pdf/${rfq.file}`);
      setShowPDF(true);
    }

    const citedContent =
      `Source RFQ: ${rfq.id}\n------------------------------------------------\n\n` +
      formatRFQContent(rfq.content);

    setEditorText(citedContent);
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">STELLANTIS</div>
        <div className="title">RFQ Generator Agent</div>
      </header>

      <div className="layout">
        {/* LEFT CHAT */}
        <div className="chat">
          <div className="chat-body">
            {chat.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                {m.text}
              </div>
            ))}
          </div>

          <div className="chat-input">
            <input
              placeholder="Give input requirements…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button onClick={sendMessage}>➤</button>
          </div>
        </div>

        {/* RIGHT WORKSPACE */}
        <div className="workspace">
          <div className="history">
            <h3>Past RFQs</h3>

            {history.map(r => (
              <div
                key={r.id}
                className="history-item"
                onClick={() => selectRFQ(r)}
              >
                📄 {r.title}
              </div>
            ))}
          </div>

          {selectedRFQ && (
            <div className="editor">
              <div className="editor-header">
                <span>Edit RFQ</span>

                <div>
                  <button onClick={() => exportRFQ("pdf")}>Export PDF</button>
                  <button onClick={() => exportRFQ("docx")}>Export DOCX</button>
                </div>
              </div>

              <ReactQuill
                value={editorText}
                onChange={setEditorText}
                className="editor-box"
                modules={{
                  toolbar: [
                    ["bold", "italic", "underline"],
                    [{ list: "ordered" }, { list: "bullet" }],
                    ["clean"]
                  ]
                }}
              />
            </div>
          )}
        </div>
      </div>

      {/* PDF POPUP */}
      {showPDF && (
        <div className="pdf-overlay">
          <div className="pdf-container">
            <button className="close-btn" onClick={() => setShowPDF(false)}>
              ✖
            </button>

            <iframe src={pdfURL} className="pdf-popup-frame" title="RFQ PDF" />
          </div>
        </div>
      )}
    </div>
  );
}
