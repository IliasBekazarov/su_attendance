import React, { createContext, useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";
import api from "../services/api";
import { toast } from "react-toastify";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      try {
        const decoded = jwtDecode(token);
        if (decoded.role) {
          setUser({ ...decoded, token });
        } else {
          toast.error("Invalid session. Please login again.");
          localStorage.removeItem("token");
        }
      } catch (error) {
        toast.error("Invalid token. Please login again.");
        localStorage.removeItem("token");
      }
    }
    setLoading(false);
  }, []);

  const login = async (credentials) => {
    try {
      const response = await api.post("/token/", credentials);
      const { access } = response.data;
      localStorage.setItem("token", access);
      const decoded = jwtDecode(access);
      if (decoded.role) {
        setUser({ ...decoded, token: access });
        toast.success("Login successful!");
      } else {
        throw new Error("Role not found in token");
      }
    } catch (error) {
      toast.error("Login failed: " + (error.response?.data?.detail || error.message));
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    toast.info("Logged out successfully.");
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};