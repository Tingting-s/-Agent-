import { getTaskLabel } from "../utils/formatters";

function StatusBanner({ result, isLoading }) {
  if (isLoading) {
    return (
      <div className="status-banner status-loading">
        <strong>请求处理中</strong>
        <span>前端已提交请求，正在等待后端返回结果。</span>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="status-banner status-idle">
        <strong>准备就绪</strong>
        <span>选择一个任务并提交，请求状态会显示在这里。</span>
      </div>
    );
  }

  const bannerClass =
    result.status === "success"
      ? "status-success"
      : result.status === "need_more_info"
        ? "status-warning"
        : "status-error";

  return (
    <div className={`status-banner ${bannerClass}`}>
      <strong>
        {getTaskLabel(result.task_type)} / {result.status}
      </strong>
      <span>{result.message || "后端未返回 message。"}</span>
    </div>
  );
}

export default StatusBanner;
