function TaskTabs({ activeTask, onChange, options }) {
  return (
    <div className="task-tabs" role="tablist" aria-label="任务切换">
      {options.map((option) => (
        <button
          key={option.key}
          type="button"
          className={`tab-button ${activeTask === option.key ? "active" : ""}`}
          onClick={() => onChange(option.key)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export default TaskTabs;
