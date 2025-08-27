import React, { useEffect, useState } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import "./pagesCss/Dashboard.css";

// Chart.js setup
ChartJS.register(
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend
);

const Dashboard = () => {
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState("monthly"); // Default: Last Month

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await axios.get(
          `http://localhost:8000/api/dashboard-stats/?period=${period}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        setStats(response.data || {});
        setLoading(false);
      } catch (err) {
        setError("Failed to load stats");
        setLoading(false);
      }
    };
    fetchStats();
  }, [period]);

  if (loading) return <div className="dashboard-container">Loading...</div>;
  if (error) return <div className="dashboard-container error">{error}</div>;

  // Prepare chart data if trend exists
  const chartData =
    stats.trend && stats.trend.length > 0
      ? {
          labels: stats.trend.map((item) => item.date),
          datasets: [
            {
              label: "Attendance %",
              data: stats.trend.map((item) => item.attendance),
              borderColor: "#007bff",
              backgroundColor: "rgba(0, 123, 255, 0.2)",
              fill: true,
              tension: 0.3,
            },
          ],
        }
      : null;

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Attendance Trend" },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  return (
    <div className="dashboard-container">
      <h2>Dashboard</h2>
      <select
        value={period}
        onChange={(e) => setPeriod(e.target.value)}
        className="period-select"
      >
        <option value="all">All Time</option>
        <option value="monthly">Last Month</option>
      </select>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Students</h3>
          <p>{stats.students || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Total Teachers</h3>
          <p>{stats.teachers || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Total Classes</h3>
          <p>{stats.classes || 0}</p>
        </div>
        <div className="stat-card">
          <h3>Attendance %</h3>
          <p>{stats.attendance || 0}%</p>
        </div>
      </div>

      <div className="chart-container">
        {chartData ? (
          <Line data={chartData} options={chartOptions} />
        ) : (
          <p>No trend data available.</p>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
