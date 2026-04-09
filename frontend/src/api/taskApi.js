export async function executeTask(payload) {
  const response = await fetch("/api/tasks/execute", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  let data = null;

  try {
    data = await response.json();
  } catch (error) {
    if (!response.ok) {
      throw new Error("服务返回了无法解析的响应。");
    }
  }

  if (!response.ok) {
    const message =
      data?.message || data?.detail || `请求失败，状态码 ${response.status}`;
    throw new Error(message);
  }

  if (!data || typeof data !== "object") {
    throw new Error("服务返回为空，请检查后端是否正常运行。");
  }

  return data;
}
