import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './pagesCss/Attendance.css';

const Attendance = () => {
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAttendance = async () => {
      try {
        const token = localStorage.getItem('token'); // Эгерде аутентификация болсо
        const response = await axios.get('http://localhost:8000/api/attendance/', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setAttendance(response.data || []);
        setLoading(false);
      } catch (err) {
        setError('Failed to load attendance');
        setLoading(false);
      }
    };
    fetchAttendance();
  }, []);

  if (loading) return <div className="attendance-container">Loading...</div>;
  if (error) return <div className="attendance-container error">{error}</div>;

  return (
    <div className="attendance-container">
      <h2>Attendance</h2>
      <table className="attendance-table">
        <thead>
          <tr>
            <th>User</th>
            <th>Schedule</th>
            <th>Present</th>
            <th>Recorded At</th>
          </tr>
        </thead>
        <tbody>
          {attendance.map((record) => (
            <tr key={record.id}>
              <td>{record.user.username}</td>
              <td>{record.schedule.course_name}</td>
              <td>{record.is_present ? 'Yes' : 'No'}</td>
              <td>{new Date(record.recorded_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Attendance;