import {
  asArray,
  getTaskLabel,
  hasStructuredContent,
  safeValue,
  stringifyRetryCount
} from "../utils/formatters";

function EmptyState({ isLoading }) {
  return (
    <div className="empty-state">
      <h3>{isLoading ? "正在等待后端响应..." : "等待一次请求"}</h3>
      <p>
        {isLoading
          ? "请求已经发出，结果返回后会在这里展示。"
          : "请在左侧选择任务类型并提交，右侧会显示友好结果和原始 JSON。"}
      </p>
    </div>
  );
}

function KeyValueGrid({ items }) {
  return (
    <div className="key-value-grid">
      {items.map((item) => (
        <div className="kv-card" key={item.label}>
          <span className="kv-label">{item.label}</span>
          <strong className="kv-value">{safeValue(item.value)}</strong>
        </div>
      ))}
    </div>
  );
}

function ListSection({ title, items, emptyText = "暂无内容" }) {
  const normalizedItems = asArray(items);

  return (
    <section className="result-block">
      <h3>{title}</h3>
      {normalizedItems.length > 0 ? (
        <ul className="plain-list">
          {normalizedItems.map((item, index) => (
            <li key={`${title}-${index}`}>{safeValue(item)}</li>
          ))}
        </ul>
      ) : (
        <p className="muted-text">{emptyText}</p>
      )}
    </section>
  );
}

function EmailResult({ data }) {
  return (
    <>
      <KeyValueGrid
        items={[
          { label: "主题", value: data?.subject },
          { label: "语气", value: data?.tone }
        ]}
      />
      <section className="result-block">
        <h3>邮件正文</h3>
        <div className="rich-text-box">{safeValue(data?.body, "暂无正文")}</div>
      </section>
    </>
  );
}

function MeetingResult({ data }) {
  const tasks = asArray(data?.tasks);
  const participants = asArray(data?.participants);
  const decisions = asArray(data?.decisions);

  return (
    <>
      <section className="result-block">
        <h3>会议摘要</h3>
        <p>{safeValue(data?.summary, "暂无摘要")}</p>
      </section>

      <ListSection title="参会人" items={participants} emptyText="未返回参会人信息" />
      <ListSection title="决议" items={decisions} emptyText="未返回决议信息" />

      <section className="result-block">
        <h3>任务列表</h3>
        {tasks.length > 0 ? (
          <div className="table-wrap">
            <table className="result-table">
              <thead>
                <tr>
                  <th>任务名称</th>
                  <th>负责人</th>
                  <th>截止时间</th>
                  <th>优先级</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task, index) => (
                  <tr key={`task-${index}`}>
                    <td>{safeValue(task?.task_name)}</td>
                    <td>{safeValue(task?.owner)}</td>
                    <td>{safeValue(task?.deadline)}</td>
                    <td>{safeValue(task?.priority)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted-text">未返回任务列表</p>
        )}
      </section>
    </>
  );
}

function DocumentResult({ data }) {
  return (
    <>
      <section className="result-block">
        <h3>文档摘要</h3>
        <p>{safeValue(data?.summary, "暂无摘要")}</p>
      </section>
      <ListSection title="关键要点" items={data?.key_points} emptyText="未返回关键要点" />
      <ListSection title="风险项" items={data?.risks} emptyText="未返回风险项" />
    </>
  );
}

function WeatherResult({ data }) {
  return (
    <KeyValueGrid
      items={[
        { label: "城市", value: data?.city },
        { label: "天气", value: data?.condition },
        { label: "温度 (°C)", value: data?.temperature_c },
        { label: "湿度 (%)", value: data?.humidity },
        { label: "风速 (kph)", value: data?.wind_speed_kph },
        { label: "数据来源", value: data?.source }
      ]}
    />
  );
}

function GenericResult({ data }) {
  const entries = Object.entries(data || {});

  return entries.length > 0 ? (
    <div className="key-value-grid">
      {entries.map(([key, value]) => (
        <div className="kv-card" key={key}>
          <span className="kv-label">{key}</span>
          <strong className="kv-value">{Array.isArray(value) ? value.join("，") : safeValue(value)}</strong>
        </div>
      ))}
    </div>
  ) : (
    <p className="muted-text">当前没有可展示的结构化结果。</p>
  );
}

function ResultPanel({ result, isLoading }) {
  if (!result) {
    return <EmptyState isLoading={isLoading} />;
  }

  const structuredResult = result.structured_result || {};

  return (
    <div className="result-panel-body">
      <div className="result-meta">
        <span className="meta-pill">{getTaskLabel(result.task_type)}</span>
        <span className="meta-pill">{stringifyRetryCount(result.retry_count)}</span>
      </div>

      {result.task_type === "email_draft" && <EmailResult data={structuredResult} />}
      {result.task_type === "meeting_extraction" && <MeetingResult data={structuredResult} />}
      {result.task_type === "document_summary" && <DocumentResult data={structuredResult} />}
      {result.task_type === "weather_query" && <WeatherResult data={structuredResult} />}
      {!["email_draft", "meeting_extraction", "document_summary", "weather_query"].includes(result.task_type) &&
        <GenericResult data={structuredResult} />}

      {!hasStructuredContent(structuredResult) && (
        <div className="empty-inline-note">
          <p>当前响应没有返回可展示的结构化内容，可以展开下方原始 JSON 查看细节。</p>
        </div>
      )}
    </div>
  );
}

export default ResultPanel;
