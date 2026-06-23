import React from "react";
import { createRoot } from "react-dom/client";
import { CalendarDays, MessageSquare, Search } from "lucide-react";
import "./styles.css";

function App() {
  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand-mark">AI</div>
        <strong>개인 일정 관리</strong>
        <nav>
          <button className="active">월 보기</button>
          <button>주 보기</button>
          <button>일 보기</button>
        </nav>
      </aside>
      <section className="workspace">
        <header className="calendar-header">
          <button aria-label="이전">‹</button>
          <h1>AI Scheduler</h1>
          <button aria-label="다음">›</button>
        </header>
        <div className="calendar-placeholder">
          <CalendarDays size={40} />
          <p>React 캘린더 화면을 이 영역에 이식합니다.</p>
        </div>
      </section>
      <aside className="task-panel">
        <div className="panel-tools">
          <Search size={18} />
          <span>작업 메뉴</span>
        </div>
        <div className="chat-card">
          <MessageSquare size={18} />
          <span>AI 채팅과 상세 패널을 연결합니다.</span>
        </div>
      </aside>
    </main>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
