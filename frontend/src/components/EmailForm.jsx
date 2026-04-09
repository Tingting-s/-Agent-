import { useState } from "react";

const DEFAULT_VALUES = {
  user_input: "帮我生成一封项目延期说明邮件",
  subject: "项目延期说明",
  purpose: "向项目经理说明交付延期原因",
  context: "由于接口调整和测试延后，原定本周五交付时间需顺延到下周三",
  tone: "formal"
};

function EmailForm({ isLoading, onSubmit }) {
  const [formData, setFormData] = useState(DEFAULT_VALUES);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit({
      user_input: formData.user_input,
      task_type: "email_draft",
      additional_inputs: {
        subject: formData.subject,
        purpose: formData.purpose,
        context: formData.context,
        tone: formData.tone
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
        <span>subject</span>
        <input
          name="subject"
          value={formData.subject}
          onChange={handleChange}
          disabled={isLoading}
        />
      </label>

      <label className="field">
        <span>purpose</span>
        <input
          name="purpose"
          value={formData.purpose}
          onChange={handleChange}
          disabled={isLoading}
        />
      </label>

      <label className="field">
        <span>context</span>
        <textarea
          name="context"
          value={formData.context}
          onChange={handleChange}
          rows={5}
          disabled={isLoading}
        />
      </label>

      <label className="field">
        <span>tone</span>
        <select
          name="tone"
          value={formData.tone}
          onChange={handleChange}
          disabled={isLoading}
        >
          <option value="formal">formal</option>
          <option value="friendly">friendly</option>
          <option value="concise">concise</option>
        </select>
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

export default EmailForm;
