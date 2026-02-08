import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import TopNav from "../components/TopNav.jsx";
import StatCard from "../components/StatCard.jsx";
import ActivityList from "../components/ActivityList.jsx";
import GoalDonut from "../components/GoalDonut.jsx";

export default function Dashboard() {
const nav = useNavigate();

// Mock data for demo (swap with API later)
const stats = useMemo(
() => ({
    streakDays: 12,
    todayGoal: 4,
    doneToday: 1,
    carryover: 2,
}),
[]
);

const activity = useMemo(
() => [
    {
    id: 1,
    title: "Two Sum (Array / HashMap)",
    note: "Mistake: forgot to store index before checking complement.",
    difficulty: "Easy",
    status: "Completed",
    },
    {
    id: 2,
    title: "Longest Substring Without Repeating Characters",
    note: "Sliding window: move left pointer when duplicate appears.",
    difficulty: "Medium",
    status: "In Progress",
    },
    {
    id: 3,
    title: "Binary Tree Level Order Traversal",
    note: "BFS queue + per-level loop; practice edge cases.",
    difficulty: "Medium",
    status: "Review",
    },
    {
    id: 4,
    title: "Rotate List (Linked List)",
    note: "Find length, connect tail->head, cut at (n-k%n).",
    difficulty: "Medium",
    status: "Review",
    },
    {
    id: 5,
    title: "Longest Substring Without Repeating Characters",
    note: "Sliding window: move left pointer when duplicate appears.",
    difficulty: "Medium",
    status: "In Progress",
    },
    {
    id: 6,
    title: "Binary Tree Level Order Traversal",
    note: "BFS queue + per-level loop; practice edge cases.",
    difficulty: "Medium",
    status: "Review",
    },
    {
    id: 7,
    title: "Rotate List (Linked List)",
    note: "Find length, connect tail->head, cut at (n-k%n).",
    difficulty: "Medium",
    status: "Review",
    },
    {
    id: 8,
    title: "Longest Substring Without Repeating Characters",
    note: "Sliding window: move left pointer when duplicate appears.",
    difficulty: "Medium",
    status: "In Progress",
    },
    {
    id: 9,
    title: "Binary Tree Level Order Traversal",
    note: "BFS queue + per-level loop; practice edge cases.",
    difficulty: "Medium",
    status: "Review",
    },
    {
    id: 10,
    title: "Rotate List (Linked List)",
    note: "Find length, connect tail->head, cut at (n-k%n).",
    difficulty: "Medium",
    status: "Review",
    },
],
[]
);

const goalData = useMemo(() => {
const backlog = stats.carryover;
const planned = Math.max(0, stats.todayGoal - stats.doneToday - backlog);
const done = stats.doneToday;
const review = 1;

const raw = [
    { name: "Carryover", value: backlog },
    { name: "Planned", value: planned },
    { name: "Review", value: review },
    { name: "Done", value: done },
];

const total = raw.reduce((s, x) => s + x.value, 0) || 1;
return raw.map((x) => ({ ...x, pct: Math.round((x.value / total) * 100) }));
}, [stats]);

return (
<div className="app-shell">
    <TopNav />

    <div className="page">
    <div className="hero">
        <div>
        <h1 className="h1">Start Learning with Your Tutor</h1>
        <p className="muted">
            Your AI mentor tracks your LeetCode progress, goals, and reflections.
        </p>
        </div>

        <button className="primary-btn" onClick={() => nav("/tutor")}>
        Open AI Tutor →
        </button>
    </div>

    <div className="grid-4">
        <StatCard
        title="Streak"
        value={`${stats.streakDays} days`}
        subtitle="Keep momentum"
        icon="🔥"
        />

        {/* CLICK THIS ONE */}
        <StatCard
        title="Today’s Goal"
        value={`${stats.todayGoal} problems`}
        subtitle="Click to view details"
        icon="🎯"
        onClick={() => nav("/goals")}
        />

        <StatCard
        title="Done Today"
        value={`${stats.doneToday}`}
        subtitle="Completed so far"
        icon="✅"
        />

        <StatCard
        title="Carryover"
        value={`${stats.carryover}`}
        subtitle="Missed yesterday (rolled in)"
        icon="⏳"
        />
    </div>

    <div className="grid-2">
        <ActivityList items={activity} />
        <GoalDonut data={goalData} />
    </div>
    </div>
</div>
);
}
