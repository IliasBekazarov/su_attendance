// src/pages/Login.jsx
import React, { useState, useContext, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import Spinner from "../components/Spinner";
import "./pagesCss/Login.css"; // Use the same CSS file

const Login = () => {
  const [credentials, setCredentials] = useState({
    username: "",
    password: "",
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login, user } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate("/");
  }, [user, navigate]);

  const handleChange = (e) =>
    setCredentials({ ...credentials, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!credentials.username || !credentials.password) {
      setError("Please fill all fields");
      return;
    }
    setLoading(true);
    try {
      const success = await login(credentials.username, credentials.password);
      if (success) {
        navigate("/dashboard");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="content">
        <div className="container">
          {/* Login Form */}
          <div className="form-container sign-in">
            <form onSubmit={handleSubmit}>
              <h1>Welcome Back!</h1>
              <div className="social-icons">
                <a href="#">
                  <i className="fab fa-facebook-f"></i>
                </a>
                <a href="#">
                  <i className="fab fa-google-plus-g"></i>
                </a>
                <a href="#">
                  <i className="fab fa-linkedin-in"></i>
                </a>
              </div>
              <span>Use your account</span>
              <input
                type="text"
                name="username"
                placeholder="Username"
                value={credentials.username}
                onChange={handleChange}
              />
              <input
                type="password"
                name="password"
                placeholder="Password"
                value={credentials.password}
                onChange={handleChange}
              />
              {error && (
                <p style={{ color: "red", fontSize: "13px" }}>{error}</p>
              )}
              <button type="submit" disabled={loading}>
                {loading ? <Spinner /> : "Login"}
              </button>
              <p>
                Don’t have an account?{" "}
                <Link
                  to="/register"
                  style={{ color: "#512da8", fontWeight: "600" }}
                >
                  Register
                </Link>
              </p>
            </form>
          </div>

          {/* Toggle Panel */}
          <div className="toggle-container">
            <div className="toggle">
              <div className="toggle-panel toggle-right">
                <h1>Hello, Friend!</h1>
                <p>
                  Enter your personal details and start your journey with us
                </p>
                <Link to="/register">
                  <button className="hidden">Register</button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Login;
