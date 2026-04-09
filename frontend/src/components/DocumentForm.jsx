import { useState } from "react";

const DEFAULT_VALUES = {
  user_input: "请帮我总结这个文档",
  file_path: "data/sample_doc.md"
};

function DocumentForm({ isLoading, onSubmit }) {
  const [formData, setFormData] = useState(DEFAULT_VALUES);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit({
      user_input: formData.user_input,
      task_type: "document_summary",
      additional_inputs: {
        file_path: formData.file_path
      }
    });
  };

  const handleReset = () => {
    setFormData(DEFAULT_VALUES);
  };

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>user_input</span>
        <textarea
          name="user_input"
          value={formData.user_input}
          onChange={handleChange}
          rows={3}
          disabled={isLoading}
        />
      </label>

      <label className="field">
        <span>file_path</span>
        <input
          name="file_path"
          value={formData.file_path}
          onChange={handleChange}
          disabled={isLoading}
        />
      </label>

      <div className="form-actions">
        <button type="submit" className="primary-button" disabled={isLoading}>
          {isLoading ? "提交中..." : "提交请求"}
        </button>
        <button type="button" className="secondary-button" onClick={handleReset} disabled={isLoading}>
          重置默认值
        </button>
      </div>
    </form>
  );
}

export default DocumentForm;
