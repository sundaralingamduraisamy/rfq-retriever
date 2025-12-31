import "./HistoryPanel.css";

export default function HistoryPanel({ history, selectRFQ }) {
  return (
    <div className="history-box">
      <h3>Relevant RFQs</h3>

      {history.length === 0 && (
        <div className="empty-box">No RFQs yet. Search first.</div>
      )}

      <div className="rfq-list">
        {history.map((r, i) => (
          <div key={i} className="rfq-card" onClick={() => selectRFQ(r)}>
            <div className="rfq-name">{r.file}</div>
            <div className="rfq-score">Relevance: {r.score}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}
