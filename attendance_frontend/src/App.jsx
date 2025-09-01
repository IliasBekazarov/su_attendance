import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Schedule from "./pages/Schedule";
import Attendance from "./pages/Attendance";
import Reports from "./pages/Reports";
import "react-toastify/dist/ReactToastify.css";
import { AuthProvider, AuthContext } from "./context/AuthContext";
import { useContext } from "react";
import "./App.css";
const AppContent = () => {
  const { user } = useContext(AuthContext);

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }

  return (
    <div className="flex">
      
      <div className="navbar">
        <Navbar />
        <div className="content">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/schedule" element={<Schedule />} />
            <Route path="/attendance" element={<Attendance />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="*" element={<Dashboard />} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <ToastContainer position="top-right" autoClose={3000} />
        <AppContent />
      </Router>
    </AuthProvider>
  );
};

export default App;