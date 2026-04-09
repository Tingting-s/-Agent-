import { useState } from "react";

const DEFAULT_VALUES = {
  user_input: "请提取下面会议纪要中的任务项",
  meeting_text:
    "今天会议决定由张三本周五前整理需求文档，李四下周二前完成接口联调，王五负责测试用例整理。"
};

function MeetingForm({ isLoading, onSubmit }) {
  const [formData, setFormData] = useState(DEFAULT_VALUES);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit({
      user_input: formData.user_input,
      task_type: "meeting_extraction",
      additional_inputs: {
        meeting_text: formData.meeting_text
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
        <span>meeting_text</span>
        <textarea
          name="meeting_text"
          value={formData.meeting_text}
          onChange={handleChange}
          rows={8}
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

export default MeetingForm;
