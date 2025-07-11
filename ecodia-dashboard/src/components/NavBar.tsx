// src/components/NavBar.tsx
import React from "react";
import { Link, useLocation } from "react-router-dom";

const tabs = [
  { label: "Agents", to: "/Dashboard" },
  { label: "Events", to: "/Events" },
  { label: "Dreams", to: "/Dreams" },
  { label: "Logs", to: "/Logs" },
  { label: "Live Chat", to: "/LiveChat" }
];

const NavBar: React.FC = () => {
  const location = useLocation();
  return (
    <nav className="flex gap-2 mb-6">
      {tabs.map(tab => (
        <Link
          key={tab.to}
          to={tab.to}
          className={
            "px-4 py-2 rounded-lg font-medium " +
            (location.pathname === tab.to
              ? "bg-emerald-700 text-white"
              : "bg-green-100 text-emerald-900 hover:bg-green-200")
          }
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
};

export default NavBar;
