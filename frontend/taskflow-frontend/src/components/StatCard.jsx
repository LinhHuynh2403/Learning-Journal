export default function StatCard({ title, value, subtitle, icon, onClick }) {
    return (
        <div className={`card stat-card ${onClick ? "clickable" : ""}`} onClick={onClick}>
            <div className="stat-header">
            <div className="stat-title">{title}</div>
            <div className="stat-icon">{icon}</div>
            </div>
            <div className="stat-value">{value}</div>
            <div className="stat-sub">{subtitle}</div>
        </div>
    );
}
