// src/components/Navbar.jsx
import { useContext } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import "../components/stylesForComponents/Navbar.css";
import Logo from "../images/logo.jpeg";

const Navbar = () => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const roleLinks = {
    admin: [
      { to: "/dashboard", label: "Dashboard" },
      { to: "/schedule", label: "Schedule" },
      { to: "/attendance", label: "Attendance" },
      { to: "/reports", label: "Reports" },
    ],
    teacher: [
      { to: "/attendance", label: "Attendance" },
      { to: "/schedule", label: "Schedule" },
    ],
    student: [
      { to: "/schedule", label: "Schedule" },
      { to: "/attendance", label: "My Attendance" },
    ],
    parent: [{ to: "/reports", label: "Reports" }],
    manager: [
      { to: "/schedule", label: "Schedule" },
      { to: "/attendance", label: "Attendance" },
    ],
  };

  return (
    <nav className="navbar1">
      <div className="navbar-container">
        <div className="navbar-left">
          <Link to="/" className="navbar-logo">
            <div className="navbar-logo">
              <img src={Logo} alt="Logo" className="logo" />
              <div className="navbar-logo-text">
                <h3>Salymbekov</h3>
                <h4>University</h4>
              </div>
            </div>
          </Link>
        </div>

        <div className="navbar-links">
          {user &&
            roleLinks[user.role]?.map((link) => (
              <Link key={link.to} to={link.to} className="menus">
                {link.label}
              </Link>
            ))}
        </div>

        <div className="navbar-right">
          {user && (
            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
