import { useMemo, useState } from "react";
import TopNav from "../components/TopNav.jsx";
import { mentorChat } from "../services/api.js";

export default function TutorChat() {
const [messages, setMessages] = useState(() =>
[
    { role: "assistant", content: "Hey! Tell me what you’re studying today (topic + concepts you struggled with)." },
]
);
const [text, setText] = useState("");
const [loading, setLoading] = useState(false);

const canSend = useMemo(() => text.trim().length > 0 && !loading, [text, loading]);

async function send() {
if (!canSend) return;

const userMsg = { role: "user", content: text.trim() };
setMessages((m) => [...m, userMsg]);
setText("");
setLoading(true);

try {
    const res = await mentorChat({ message: userMsg.content });
    const ai = { role: "assistant", content: res.reply ?? res.message ?? "(No reply field found)" };
    setMessages((m) => [...m, ai]);
} catch (e) {
    setMessages((m) => [
    ...m,
    { role: "assistant", content: `Demo mode: backend not connected. (Error: ${e.message})\n\nTry: “Explain sliding window for longest substring.”` },
    ]);
} finally {
    setLoading(false);
}
}

return (
<div className="app-shell">
    <TopNav />

    <div className="page">
    <div className="chat-card card">
        <div className="card-title-row">
        <div className="card-title">AI Tutor</div>
        <div className="card-subtitle">Ask for hints, plan today’s work, or review mistakes</div>
        </div>

        <div className="chat-window">
        {messages.map((m, idx) => (
            <div key={idx} className={`bubble-row ${m.role}`}>
            <div className={`bubble ${m.role}`}>{m.content}</div>
            </div>
        ))}
        {loading && (
            <div className="bubble-row assistant">
            <div className="bubble assistant">Thinking…</div>
            </div>
        )}
        </div>

        <div className="chat-input">
        <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type your question… (e.g., ‘Help me debug Rotate List’) "
            rows={2}
        />
        <button className="primary-btn" onClick={send} disabled={!canSend}>
            Send
        </button>
        </div>
    </div>
    </div>
</div>
);
}
