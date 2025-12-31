import { useState, useEffect, useRef } from "react";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import "./App.css";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [input, setInput] = useState("");
  const [chat, setChat] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedRFQ, setSelectedRFQ] = useState(null);

  const [editorText, setEditorText] = useState("");
  const [originalRFQ, setOriginalRFQ] = useState("");

  const [pdfURL, setPdfURL] = useState("");
  const [showPDF, setShowPDF] = useState(false);

  const analyzeTimer = useRef(null);
  const [awaitingDecision, setAwaitingDecision] = useState(false);

  const [clarifyMode, setClarifyMode] = useState(false);
  const [qIndex, setQIndex] = useState(0);
  const [answers, setAnswers] = useState({ requirement: "" });

  const QUESTIONS = [
    "️What quantity is required?",
    "What is the expected delivery timeline? (in weeks)",
    "Do you require installation support? (Yes/No)",
    "Required warranty period?",
    "Any mandatory compliance standards?"
  ];

  useEffect(() => {
    async function greet() {
      try {
        const res = await fetch(`${API}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            history: [],
            user_message: "start_session",
            selected_rfq: null
          })
        });

        const data = await res.json();

        setChat([
          {
            role: "agent",
            text: data.reply || "Hello! I'm ready to help you with RFQs."
          }
        ]);
      } catch (e) {
        setChat([
          {
            role: "agent",
            text: "Hello! I'm your RFQ Assistant. Tell me what you need 😊"
          }
        ]);
      }
    }

    greet();
  }, []);

  // -------------------------------
  // UPDATED FORMATTER (ONLY FIXED PART)
  // -------------------------------
 function convertToHTML(text) {
  if (!text) return "";

  let html = text;

  // Remove accidental bold markers
  html = html.replace(/\*\*/g, "");

  const sections = [
    "BACKGROUND & OBJECTIVE",
    "SCOPE OF WORK",
    "TECHNICAL REQUIREMENTS",
    "SERVICE LEVEL AGREEMENT",
    "COMPLIANCE & STANDARDS",
    "COMMERCIAL TERMS",
    "DELIVERY TIMELINE",
    "EVALUATION CRITERIA",
    "REVISION HISTORY"
  ];

  // Force headings to proper block format
  sections.forEach(sec => {
    const regex = new RegExp(sec, "g");
    html = html.replace(
      regex,
      `</p><h3 style="font-weight:700;margin-top:12px;">${sec}</h3><p>`
    );
  });

  // Clean double paragraph breaks
  html = html.replace(/<\/p><p><\/p><p>/g, "</p><p>");

  // Replace actual paragraph spacing
  html = html.replace(/\n\n/g, "</p><p>");

  // Line breaks
  html = html.replace(/\n/g, "<br/>");

  // Bullet points ONLY if line starts with bullet
  html = html.replace(/^•\s*/gm, "<br/>• ");
  html = html.replace(/^-\s*/gm, "<br/>• ");

  return `<p>${html}</p>`;
}

  function htmlToPlain(html) {
    return html.replace(/<[^>]+>/g, "").trim();
  }

  function normalize(t) {
    return t.replace(/\s+/g, " ").trim();
  }

  function autoApplySmartFixes(agentReply) {
    if (!editorText) return;

    let plain = htmlToPlain(editorText);
    let changed = false;

    const percentRegex = /(\d+)\s*%\s*(?:to|→)\s*(\d+)%/i;
    const p = agentReply.match(percentRegex);

    if (p) {
      const oldVal = p[1];
      const newVal = p[2];

      if (plain.includes(`${oldVal}%`)) {
        plain = plain.replaceAll(`${oldVal}%`, `${newVal}%`);
        changed = true;
      }
    }

    const deliveryRegex = /(\d+)\s*days\s*(?:to|→)\s*(\d+)\s*days/i;
    const d = agentReply.match(deliveryRegex);

    if (d) {
      const oldDay = d[1];
      const newDay = d[2];

      const reg = new RegExp(`${oldDay}\\s*days`, "gi");
      plain = plain.replace(reg, `${newDay} days`);
      changed = true;
    }

    if (!changed) return;

    const html = convertToHTML(plain);
    setEditorText(html);
    setOriginalRFQ(plain);

    setChat(c => [
      ...c,
      { role: "agent", text: "✍️ Applied recommended RFQ update automatically." }
    ]);
  }

  function isStrictRFQ(text) {
    if (!text) return false;

    if (text.includes("🔎 RFQ Impact Analysis")) return false;
    if (text.toLowerCase().includes("recommendations")) return false;
    if (text.toLowerCase().includes("what changed")) return false;

    const must = [
      "BACKGROUND & OBJECTIVE",
      "SCOPE OF WORK",
      "TECHNICAL REQUIREMENTS"
    ];

    let count = 0;
    must.forEach(s => text.includes(s) && count++);

    return count >= 2;
  }

  async function naturalChat(userMsg) {
    const res = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        history: chat,
        user_message: userMsg,
        selected_rfq: selectedRFQ?.file || null
      })
    });

    const data = await res.json();
    const text = data.reply || "";

    setChat((c) => [...c, { role: "agent", text }]);

    if (isStrictRFQ(text)) {
      const html = convertToHTML(text);
      setEditorText(html);
      setOriginalRFQ(htmlToPlain(html));
    }

    autoApplySmartFixes(text);
  }

  async function handleClarificationFlow(userMsg) {
    if (qIndex === 0) {
      setAnswers((a) => ({ ...a, requirement: userMsg }));
      setChat(c => [...c, { role: "agent", text: QUESTIONS[0] }]);
      setQIndex(1);
      return;
    }

    const keys = ["quantity", "delivery", "installation", "warranty", "compliance"];
    const key = keys[qIndex - 1];

    setAnswers(a => ({ ...a, [key]: userMsg }));

    if (qIndex < QUESTIONS.length) {
      setChat(c => [...c, { role: "agent", text: QUESTIONS[qIndex] }]);
      setQIndex(qIndex + 1);
      return;
    }

    const payload = {
      requirement: answers.requirement,
      filled_data: answers,
      reference_file: selectedRFQ?.file || "N/A"
    };

    const res = await fetch(`${API}/generate_final_rfq`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    const html = convertToHTML(data.draft);
    setEditorText(html);
    setOriginalRFQ(htmlToPlain(html));

    setChat(c => [
      ...c,
      { role: "agent", text: "✅ Generated OEM-Grade RFQ Draft and loaded into editor." }
    ]);

    setClarifyMode(false);
    setQIndex(0);
  }

  async function sendMessage() {
    if (!input.trim()) return;

    const userMsg = input;
    setChat((c) => [...c, { role: "user", text: userMsg }]);
    setInput("");

    if (clarifyMode) {
      await handleClarificationFlow(userMsg);
      return;
    }

    if (
      userMsg.toLowerCase().includes("new rfq") ||
      userMsg.toLowerCase().includes("create rfq") ||
      userMsg.toLowerCase().includes("build rfq") ||
      userMsg.toLowerCase().includes("start rfq")
    ) {
      setClarifyMode(true);
      setChat(c => [
        ...c,
        { role: "agent", text: "Great 👍 Let’s build a professional OEM RFQ." },
        { role: "agent", text: "First, describe your requirement." }
      ]);
      return;
    }

    if (awaitingDecision) {
      if (userMsg.toLowerCase().includes("new")) {
        setEditorText("");
        setOriginalRFQ("");
        setHistory([]);
        setSelectedRFQ(null);
        setAwaitingDecision(false);

        setChat((c)=>[
          ...c,
          {role:"agent", text:"👍 Cleared previous RFQ. Tell me your new requirement!"}
        ]);

        return;
      }

      if (userMsg.toLowerCase().includes("continue")) {
        setAwaitingDecision(false);

        setChat((c)=>[
          ...c,
          {role:"agent", text:"👌 Sure. You can continue editing the same RFQ."}
        ]);

        return;
      }

      setChat((c)=>[
        ...c,
        {role:"agent", text:"Please reply with either 'new' or 'continue' 😊"}
      ]);

      return;
    }

    if (history.length > 0 || selectedRFQ) {
      await naturalChat(userMsg);
      return;
    }

    const validate = await fetch(`${API}/validate_requirement`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ requirement: userMsg })
    });

    const validRes = await validate.json();

    if (!validRes.valid) {
      setChat((c) => [
        ...c,
        { role: "agent", text: validRes.message }
      ]);
      return;
    }

    setChat((c) => [
      ...c,
      { role: "agent", text: "Great 👍 Valid Automobile Requirement." },
      { role: "agent", text: "Fetching best matching RFQs..." }
    ]);

    const search = await fetch(`${API}/search_rfq`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: userMsg })
    });

    const data = await search.json();

    const normalized = data.results.map((r, idx) => ({
      id: idx + 1,
      title: `${r.file} (score ${r.score})`,
      file: r.file
    }));

    setHistory(normalized);

    setChat((c) => [
      ...c,
      { role: "agent", text: "Top RFQs listed on right ➡️ Click one to view." }
    ]);
  }

  function selectRFQ(rfq) {
    setSelectedRFQ(rfq);
    setPdfURL(`http://127.0.0.1:8000/rfq_pdf/${rfq.file}`);
    setShowPDF(true);
  }

  async function loadRFQToEditor() {
    if (!selectedRFQ) return;

    const res = await fetch(`${API}/rfq_text/${selectedRFQ.file}`);
    const data = await res.json();

    const html = convertToHTML(data.text);

    setEditorText(html);
    setOriginalRFQ(data.text);
  }

  async function analyzeChanges(newHTML) {
    const newPlain = htmlToPlain(newHTML);

    if (!originalRFQ) return;

    const normOld = normalize(originalRFQ);
    const normNew = normalize(newPlain);

    if (normOld === normNew) return;
    if (Math.abs(normOld.length - normNew.length) < 8) return;

    const digitsOld = normOld.replace(/[^\d]/g, "");
    const digitsNew = normNew.replace(/[^\d]/g, "");
    if (digitsOld === digitsNew) return;

    const res = await fetch(`${API}/analyze_changes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        old_text: originalRFQ,
        new_text: newPlain
      })
    });

    const data = await res.json();

    setChat((c) => [
      ...c,
      { role: "agent", text: `🔎 RFQ Impact Analysis:\n${data.analysis}` }
    ]);
  }

  function handleEditorChange(value) {
    setEditorText(value);

    if (analyzeTimer.current) clearTimeout(analyzeTimer.current);

    analyzeTimer.current = setTimeout(() => {
      analyzeChanges(value);
    }, 1500);
  }

  async function exportPDF() {
    if (!editorText.trim()) return alert("No RFQ content!");

    const plain = htmlToPlain(editorText);

    const res = await fetch(`${API}/export/pdf`, {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: plain
    });

    const data = await res.json();
    window.open(`http://127.0.0.1:8000/${data.path}`, "_blank");

    setAwaitingDecision(true);

    setChat((c)=>[
      ...c,
      {
        role:"agent",
        text:
`✅ RFQ Exported Successfully.
Do you want to:
1️⃣ Generate New RFQ
2️⃣ Continue Editing This RFQ
Type "new" or "continue".`
      }
    ]);
  }

  async function exportDOCX() {
    if (!editorText.trim()) return alert("No RFQ content!");

    const plain = htmlToPlain(editorText);

    const res = await fetch(`${API}/export/docx`, {
      method: "POST",
      headers: { "Content-Type": "text/plain" },
      body: plain
    });

    const data = await res.json();
    window.open(`http://127.0.0.1:8000/${data.path}`, "_blank");

    setAwaitingDecision(true);

    setChat((c)=>[
      ...c,
      {
        role:"agent",
        text:
`✅ RFQ Exported Successfully.
Do you want to:
1️⃣ Generate New RFQ
2️⃣ Continue Editing This RFQ
Type "new" or "continue".`
      }
    ]);
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">STELLANTIS</div>
        <div className="title">RFQ Generator Agent</div>
      </header>

      <div className="layout">
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

        <div className="workspace">
          <div className="history">
            <h3>Past RFQs</h3>

            {history.map((r) => (
              <div
                key={r.id}
                className="history-item"
                onClick={() => selectRFQ(r)}
              >
                📄 {r.title}
              </div>
            ))}
          </div>

          {editorText && (
            <div className="editor">
              <div className="editor-header">
                <span>Edit RFQ</span>

                <div>
                  <button onClick={exportPDF}>Export PDF</button>
                  <button onClick={exportDOCX}>Export DOCX</button>
                </div>
              </div>

              <ReactQuill
                value={editorText}
                onChange={handleEditorChange}
                className="editor-box"
              />
            </div>
          )}
        </div>
      </div>

      {showPDF && (
        <div className="pdf-overlay">
          <div className="pdf-container">
            <div className="pdf-top-bar">
              <button className="close-btn" onClick={() => setShowPDF(false)}>
                ✖
              </button>

              <button
                className="draft-btn"
                onClick={async () => {
                  await loadRFQToEditor();
                  setShowPDF(false);
                  setChat((c) => [
                    ...c,
                    {
                      role: "agent",
                      text:
                        "Loaded RFQ into editor. Make your edits — I’ll analyze impact automatically."
                    }
                  ]);
                }}
              >
                Draft RFQ
              </button>
            </div>

            <iframe src={pdfURL} className="pdf-popup-frame" title="RFQ PDF" />
          </div>
        </div>
      )}
    </div>
  );
}
