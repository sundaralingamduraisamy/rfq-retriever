export default function ChatPanel({ chat, input, setInput, sendMessage }) {
  return (
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
          placeholder="Give RFQ requirement…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage}>➤</button>
      </div>
    </div>
  );
}
