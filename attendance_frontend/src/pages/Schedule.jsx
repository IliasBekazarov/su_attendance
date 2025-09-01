import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import api from '../services/api';
import Table from '../components/Table';
import Spinner from '../components/Spinner';

const Schedule = () => {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSchedules = async () => {
      try {
        const response = await api.get('/schedule/');
        setSchedules(response.data);
      } catch (error) {
        toast.error('Failed to load schedules');
      } finally {
        setLoading(false);
      }
    };
    fetchSchedules();
  }, []);

  const columns = [
    { header: 'ID', accessor: 'id' },
    { header: 'Group', accessor: 'group_id' },
    { header: 'Date', accessor: 'date' },
    { header: 'Time', accessor: 'time' },
    { header: 'Subject', accessor: 'subject' },
  ];

  if (loading) {
    return <Spinner />;
  }

  return (
    <div className="container mx-auto">
      <h1 className="text-2xl font-bold mb-6">Расписание</h1>
      <Table columns={columns} data={schedules} />
    </div>
  );
};

export default Schedule;