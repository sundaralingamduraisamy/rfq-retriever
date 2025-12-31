import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";

export default function RFQEditor({ editorText, setEditorText, exportPDF, exportDOC }) {
  if (!editorText) return null;

  return (
    <div className="editor">
      <div className="editor-header">
        <span>Edit RFQ</span>

        <div>
          <button onClick={exportPDF}>Export PDF</button>
          <button onClick={exportDOC}>Export DOCX</button>
        </div>
      </div>

      <ReactQuill
        value={editorText}
        onChange={setEditorText}
        modules={{
          toolbar: [
            ["bold", "italic", "underline"],
            [{ list: "ordered" }, { list: "bullet" }],
            ["clean"],
          ],
        }}
      />
    </div>
  );
}
