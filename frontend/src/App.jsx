import { useMemo, useState } from "react";
import { executeTask } from "./api/taskApi";
import TaskTabs from "./components/TaskTabs";
import EmailForm from "./components/EmailForm";
import MeetingForm from "./components/MeetingForm";
import DocumentForm from "./components/DocumentForm";
import WeatherForm from "./components/WeatherForm";
import ResultPanel from "./components/ResultPanel";
import StatusBanner from "./components/StatusBanner";
import RawJsonPanel from "./components/RawJsonPanel";
import { getTaskLabel } from "./utils/formatters";

const TASK_OPTIONS = [
  { key: "email_draft", label: "邮件草稿" },
  { key: "meeting_extraction", label: "会议任务提取" },
  { key: "document_summary", label: "文档总结" },
  { key: "weather_query", label: "天气查询" }
];

function App() {
  const [activeTask, setActiveTask] = useState("email_draft");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);

  const activeTaskLabel = useMemo(() => getTaskLabel(activeTask), [activeTask]);

  const handleSubmit = async (payload) => {
    setIsLoading(true);
    setResult(null);

    try {
      const data = await executeTask(payload);
      setResult(data);
    } catch (error) {
      setResult({
        task_type: payload.task_type,
        status: "error",
        message: error.message || "请求失败，请稍后重试。",
        structured_result: {},
        retry_count: 0
      });
    } finally {
      setIsLoading(false);
    }
  };

  const renderForm = () => {
    switch (activeTask) {
      case "meeting_extraction":
        return <MeetingForm isLoading={isLoading} onSubmit={handleSubmit} />;
      case "document_summary":
        return <DocumentForm isLoading={isLoading} onSubmit={handleSubmit} />;
      case "weather_query":
        return <WeatherForm isLoading={isLoading} onSubmit={handleSubmit} />;
      case "email_draft":
      default:
        return <EmailForm isLoading={isLoading} onSubmit={handleSubmit} />;
    }
  };

  return (
    <div className="page-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Frontend Demo</p>
          <h1>Multi Tool Agent Office Assistant</h1>
          <p className="hero-subtitle">
            一个用于演示 FastAPI <code>/tasks/execute</code> 接口的单页前端。左侧发起任务，右侧查看结构化结果。
          </p>
        </div>
      </header>

      <main className="workspace-grid">
        <section className="panel panel-form">
          <div className="panel-header">
            <div>
              <h2>任务表单区</h2>
              <p>当前任务：{activeTaskLabel}</p>
            </div>
          </div>

          <TaskTabs activeTask={activeTask} onChange={setActiveTask} options={TASK_OPTIONS} />

          <div className="form-region">{renderForm()}</div>
        </section>

        <section className="panel panel-result">
          <div className="panel-header">
            <div>
              <h2>结果展示区</h2>
              <p>展示后端返回的消息、结构化结果和原始 JSON。</p>
            </div>
          </div>

          <StatusBanner result={result} isLoading={isLoading} />
          <ResultPanel result={result} isLoading={isLoading} />
          <RawJsonPanel result={result} />
        </section>
      </main>
    </div>
  );
}

export default App;
