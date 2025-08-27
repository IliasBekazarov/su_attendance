import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './pagesCss/Reports.css';

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportType, setReportType] = useState('daily'); // Default report type

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const token = localStorage.getItem('token'); // JWT токен
        const response = await axios.get(`http://localhost:8000/api/reports/${reportType}/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setReports(response.data || []);
        setLoading(false);
      } catch (err) {
        setError('Failed to load reports');
        console.error(err);
        setLoading(false);
      }
    };
    fetchReports();
  }, [reportType]);

  const handleExport = async (format) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`http://localhost:8000/api/reports/export/${format}/`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob' // CSV же PDF файл үчүн
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report.${format}`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      setError('Failed to export report');
      console.error(err);
    }
  };

  if (loading) return <div className="reports-container">Loading...</div>;
  if (error) return <div className="reports-container error">{error}</div>;

  return (
    <div className="reports-container">
      <h2>Reports</h2>
      <div className="report-controls">
        <select
          value={reportType}
          onChange={(e) => setReportType(e.target.value)}
          className="report-select"
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
        <button onClick={() => handleExport('csv')} className="export-btn">Export CSV</button>
        <button onClick={() => handleExport('pdf')} className="export-btn">Export PDF</button>
      </div>
      {reports.length > 0 ? (
        <table className="reports-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Count</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report, index) => (
              <tr key={index}>
                <td>{report.status || 'N/A'}</td>
                <td>{report.count || 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="no-data">No reports available.</p>
      )}
    </div>
  );
};

export default Reports;