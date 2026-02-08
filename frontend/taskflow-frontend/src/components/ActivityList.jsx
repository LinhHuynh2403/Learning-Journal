export default function ActivityList({ items }) {
return (
    <div className="card">
        <div className="card-title-row">
        <div className="card-title">Recent LeetCode Activity</div>
        <div className="card-subtitle">Your latest problems + notes</div>
        </div>

        <div className="list scroll-area">
        {items.map((it) => (
            <div key={it.id} className="list-item">
            <div className="li-left">
                <div className="li-title">{it.title}</div>
                <div className="li-desc">{it.note}</div>
            </div>

            <div className="li-right">
                <span className={`pill ${it.difficulty.toLowerCase()}`}>
                {it.difficulty}
                </span>
                <span className={`pill status ${it.status.toLowerCase().replaceAll(" ", "-")}`}>
                {it.status}
                </span>
            </div>
            </div>
        ))}
        </div>
    </div>
);
}
