import { createContext, useState, useEffect } from "react";
import api from "../services/api";
import { toast } from "react-toastify";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      api
        .get("/profile/")
        .then((response) => {
          setUser(response.data);
          setLoading(false);
        })
        .catch(() => {
          localStorage.removeItem("token");
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    try {
      if (!username || !password) {
        throw new Error("Username and password are required");
      }
      console.log("Sending:", { username, password }); // Debugging
      const response = await api.post(
        "/token/",
        { username, password },
        {
          headers: { "Content-Type": "application/json" },
        }
      );
      console.log("Response:", response.data); // Debugging
      localStorage.setItem("token", response.data.access);
      const profile = await api.get("/profile/");
      setUser(profile.data);
      toast.success("Successfully logged in");
      return true;
    } catch (error) {
      console.error("Login error:", error.response?.data || error.message); // Debugging
      toast.error(
        "Login failed: " + (error.response?.data?.detail || error.message)
      );
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    toast.success("Logged out");
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
