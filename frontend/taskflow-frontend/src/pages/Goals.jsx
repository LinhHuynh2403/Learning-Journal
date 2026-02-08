import { useMemo } from "react";
import TopNav from "../components/TopNav.jsx";

export default function Goals() {
// mock for now — later pull from backend: “yesterday mentor plan”
const yesterdayPlan = useMemo(() => ({
date: "Yesterday",
focus: "Sliding Window + Linked List",
problems: [
    { id: 1, title: "3. Longest Substring Without Repeating Characters", reason: "Practice window expansion + shrink on duplicates" },
    { id: 2, title: "424. Longest Repeating Character Replacement", reason: "Classic maxFreq window trick" },
    { id: 3, title: "61. Rotate List", reason: "Pointer math + cycle break" },
    { id: 4, title: "61. Rotate List", reason: "Pointer math + cycle break" },
]
}), []);

return (
<div className="app-shell">
    <TopNav />
    <div className="page">
    <h1 className="h1">Today’s Goal Details</h1>
    <p className="muted">Problems your AI Tutor suggested from {yesterdayPlan.date}.</p>

    <div className="card" style={{ padding: 16, marginTop: 14 }}>
        <div style={{ fontWeight: 750, marginBottom: 8 }}>{yesterdayPlan.focus}</div>

        {yesterdayPlan.problems.map(p => (
        <div key={p.id} className="list-item" style={{ margin: "10px 0" }}>
            <div className="li-left">
            <div className="li-title">{p.title}</div>
            <div className="li-desc">{p.reason}</div>
            </div>
            <div className="li-right">
            <span className="pill status in-progress">To Do</span>
            </div>
        </div>
        ))}
    </div>
    </div>
</div>
);
}
