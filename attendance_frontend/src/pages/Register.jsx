// src/pages/Register.jsx
import React, { useState, useContext } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import "./pagesCss/Register.css";
const Register = () => {
  const [data, setData] = useState({
    username: "",
    email: "",
    password: "",
    password2: "",
    role: "student",
  });
  const { register } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleChange = (e) =>
    setData({ ...data, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (data.password !== data.password2) {
        alert("Passwords do not match!");
        return;
      }
      await register(data);
      navigate("/login");
    } catch (error) {
      console.error("Registration failed:", error);
    }
  };

  return (
    <>
      <div className="content">
        <div className="container active">
          {/* Register Form */}
          <div className="form-container sign-up">
            <form onSubmit={handleSubmit}>
              <h1>Create Account</h1>
             
              <span>Use your email for registration</span>
              <input
                type="text"
                name="username"
                placeholder="Username"
                value={data.username}
                onChange={handleChange}
              />
              <input
                type="email"
                name="email"
                placeholder="Email"
                value={data.email}
                onChange={handleChange}
              />
              <input
                type="password"
                name="password"
                placeholder="Password"
                value={data.password}
                onChange={handleChange}
              />
              <input
                type="password"
                name="password2"
                placeholder="Confirm Password"
                value={data.password2}
                onChange={handleChange}
              />
              <select
                name="role"
                value={data.role}
                onChange={handleChange}
                style={{
                  backgroundColor: "#eee",
                  border: "none",
                  margin: "8px 0",
                  padding: "10px 15px",
                  fontSize: "13px",
                  borderRadius: "8px",
                  width: "100%",
                  outline: "none",
                }}
              >
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
                <option value="parent">Parent</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
              <button type="submit">Register</button>
              <p>
                Already have an account?{" "}
                <Link
                  to="/login"
                  style={{ color: "#512da8", fontWeight: "600" }}
                >
                  Login
                </Link>
              </p>
            </form>
          </div>

          {/* Toggle Panel */}
          <div className="toggle-container">
            <div className="toggle">
              <div className="toggle-panel toggle-left">
                <h1>Welcome Back!</h1>
                <p>
                  To keep connected with us, please login with your personal
                  info
                </p>
                <Link to="/login">
                  <button className="hidden">Login</button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Register;
