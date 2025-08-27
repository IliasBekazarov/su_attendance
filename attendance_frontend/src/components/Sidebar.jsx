// src/components/Sidebar.jsx
import { useState } from "react";
import { Link } from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

const Sidebar = () => {
  const { user } = useContext(AuthContext);
  const [isOpen, setIsOpen] = useState(false);

  const roleLinks = {
    admin: [{ to: "/dashboard", label: "Dashboard" }, { to: "/schedule", label: "Schedule" }, { to: "/attendance", label: "Attendance" }, { to: "/reports", label: "Reports" }],
    teacher: [{ to: "/attendance", label: "Attendance" }, { to: "/schedule", label: "Schedule" }],
    student: [{ to: "/schedule", label: "Schedule" }, { to: "/attendance", label: "My Attendance" }],
    parent: [{ to: "/reports", label: "Reports" }],
    manager: [{ to: "/schedule", label: "Schedule" }, { to: "/attendance", label: "Attendance" }],
  };

  return (
    <div className="bg-white shadow-soft h-screen w-64 fixed md:static md:translate-x-0 transition-transform duration-300 ease-in-out">
      <div className="p-6">
        
        <nav className={`${isOpen ? "block" : "hidden"} md:block`}>
          {user && roleLinks[user.role]?.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="block py-2 px-4 text-gray-700 hover:bg-primary hover:text-white rounded transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
};

export default Sidebar;