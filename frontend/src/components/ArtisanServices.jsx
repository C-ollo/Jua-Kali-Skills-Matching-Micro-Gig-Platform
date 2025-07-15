import React, { useState, useEffect } from 'react';
import axios from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

function ArtisanServices() {
  const { user } = useAuth();
  const [applications, setApplications] = useState([]);
  const [assignedJobs, setAssignedJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchArtisanData = async () => {
      if (!user || user.user_type !== 'artisan') {
        setLoading(false);
        return;
      }

      try {
        const applicationsResponse = await axios.get('/jobs/applications/me');
        setApplications(applicationsResponse.data);

        const assignedJobsResponse = await axios.get('/jobs/assigned/me');
        setAssignedJobs(assignedJobsResponse.data);

      } catch (err) {
        console.error('Error fetching artisan data:', err);
        setError('Failed to load your services data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchArtisanData();
  }, [user]);

  if (loading) {
    return <p className="text-brand-text-secondary">Loading your services...</p>;
  }

  if (error) {
    return <p className="text-red-500">{error}</p>;
  }

  if (!user || user.user_type !== 'artisan') {
    return <p className="text-brand-text-secondary">This section is for artisans only.</p>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-xl font-semibold text-brand-text-primary mb-4">My Submitted Applications</h3>
        {applications.length === 0 ? (
          <p className="text-brand-text-secondary">You haven't submitted any job applications yet.</p>
        ) : (
          <ul className="space-y-3">
            {applications.map((app) => (
              <li key={app.id} className="bg-white p-3 rounded-md shadow-sm border border-brand-border">
                <p className="text-lg font-semibold text-brand-text-primary">Job: {app.job.title}</p>
                <p className="text-brand-text-secondary text-sm">Bid: ${app.bid_amount} | Status: {app.status}</p>
                <p className="text-brand-text-secondary text-xs">Message: {app.message}</p>
                <p className="text-brand-text-secondary text-xs">Applied on: {new Date(app.created_at).toLocaleDateString()}</p>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <h3 className="text-xl font-semibold text-brand-text-primary mb-4">My Assigned Jobs</h3>
        {assignedJobs.length === 0 ? (
          <p className="text-brand-text-secondary">You don't have any assigned jobs yet.</p>
        ) : (
          <ul className="space-y-3">
            {assignedJobs.map((job) => (
              <li key={job.id} className="bg-white p-3 rounded-md shadow-sm border border-brand-border">
                <p className="text-lg font-semibold text-brand-text-primary">Job: {job.title}</p>
                <p className="text-brand-text-secondary text-sm">Location: {job.location} | Budget: ${job.budget} | Status: {job.status}</p>
                {job.required_skills && job.required_skills.length > 0 && (
                  <p className="text-brand-text-secondary text-xs">Skills: {job.required_skills.join(', ')}</p>
                )}
                <p className="text-brand-text-secondary text-xs">Assigned on: {new Date(job.created_at).toLocaleDateString()}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default ArtisanServices;
