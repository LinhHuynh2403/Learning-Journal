import { Link, useLocation } from "react-router-dom";

const NavItem = ({ to, label }) => {
const loc = useLocation();
const active = loc.pathname === to;
    return (
        <Link
            to={to}
            className={`nav-item ${active ? "nav-item-active" : ""}`}
        >
            {label}
        </Link>
    );
};

export default function TopNav() {
    return (
        <div className="topbar">
            <div className="brand">
            <span className="brand-check">✓</span>
            <span className="brand-name">TaskFlow</span>
            </div>

            <div className="nav">
            <NavItem to="/" label="Dashboard" />
            <NavItem to="/tutor" label="AI Tutor" />
            </div>

            <div className="topbar-right">
            <button className="icon-btn" title="Settings">⚙️</button>
            </div>
        </div>
    );
}
