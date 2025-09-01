// src/pages/Dashboard.jsx
import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import Card from "../components/Card";

const Dashboard = () => {
  const { user } = useContext(AuthContext);

  const dashboardContent = {
    admin: { title: "Admin Dashboard", stats: ["Total Students: 50", "Teachers: 5"] },
    teacher: { title: "Teacher Dashboard", stats: ["Classes: 3", "Attendance: 90%"] },
    student: { title: "Student Dashboard", stats: ["My Attendance: 95%"] },
    parent: { title: "Parent Dashboard", stats: ["Child Attendance: 92%"] },
    manager: { title: "Manager Dashboard", stats: ["Schedules: 10", "Reports: 5"] },
  };

  const content = dashboardContent[user?.role] || { title: "Dashboard", stats: [] };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-primary mb-6">{content.title}</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {content.stats.map((stat, index) => (
          <Card key={index}>{stat}</Card>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;