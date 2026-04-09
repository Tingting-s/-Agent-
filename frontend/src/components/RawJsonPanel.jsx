import { prettyJson } from "../utils/formatters";

function RawJsonPanel({ result }) {
  return (
    <details className="raw-json-panel">
      <summary>查看原始 JSON</summary>
      <pre>{result ? prettyJson(result) : "等待请求结果..."}</pre>
    </details>
  );
}

export default RawJsonPanel;
