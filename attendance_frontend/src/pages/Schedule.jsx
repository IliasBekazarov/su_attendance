import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './pagesCss/Schedule.css';

const Schedule = () => {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSchedules = async () => {
      try {
        const token = localStorage.getItem('token'); // Эгерде аутентификация болсо
        const response = await axios.get('http://localhost:8000/api/schedule/', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSchedules(response.data || []);
        setLoading(false);
      } catch (err) {
        setError('Failed to load schedules');
        setLoading(false);
      }
    };
    fetchSchedules();
  }, []);

  if (loading) return <div className="schedule-container">Loading...</div>;
  if (error) return <div className="schedule-container error">{error}</div>;

  return (
    <div className="schedule-container">
      <h2>Schedule</h2>
      <table className="schedule-table">
        <thead>
          <tr>
            <th>Course</th>
            <th>Group</th>
            <th>Period</th>
            <th>Time</th>
            <th>Subject</th>
          </tr>
        </thead>
        <tbody>
          {schedules.map((schedule) => (
            <tr key={schedule.id}>
              <td>{schedule.course_name}</td>
              <td>{schedule.group_name}</td>
              <td>{schedule.period}</td>
              <td>{schedule.time}</td>
              <td>{schedule.subject}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Schedule;