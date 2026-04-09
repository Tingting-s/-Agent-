const TASK_LABELS = {
  email_draft: "邮件草稿",
  meeting_extraction: "会议任务提取",
  document_summary: "文档总结",
  weather_query: "天气查询"
};

export function getTaskLabel(taskType) {
  return TASK_LABELS[taskType] || taskType || "未知任务";
}

export function prettyJson(value) {
  return JSON.stringify(value, null, 2);
}

export function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export function safeValue(value, fallback = "未返回") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  return String(value);
}

export function stringifyRetryCount(value) {
  const count = Number.isFinite(value) ? value : 0;
  return `retry_count: ${count}`;
}

export function hasStructuredContent(value) {
  return Boolean(value && typeof value === "object" && Object.keys(value).length > 0);
}
