import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from '../api/axios';
import { useAuth } from '../contexts/AuthContext';
import ApplyForJobForm from '../components/ApplyForJobForm';
import ReviewForm from '../components/ReviewForm';

function JobDetailPage() {
  const { job_id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [applications, setApplications] = useState([]);
  const [applicationsLoading, setApplicationsLoading] = useState(true);
  const [applicationsError, setApplicationsError] = useState('');
  const { user, isAuthenticated, logout } = useAuth();

  useEffect(() => {
    const fetchJobDetails = async () => {
      try {
        const response = await axios.get(`/jobs/${job_id}`);
        setJob(response.data);
      } catch (err) {
        console.error('Error fetching job details:', err);
        setError('Failed to load job details. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchJobDetails();
  }, [job_id]);

  useEffect(() => {
    const fetchApplications = async () => {
      if (!user || user.user_type !== 'client' || !job || user.id !== job.client_id) {
        setApplicationsLoading(false);
        return;
      }
      try {
        const response = await axios.get(`/jobs/${job_id}/applications`);
        setApplications(response.data);
      } catch (err) {
        console.error('Error fetching applications:', err);
        setApplicationsError('Failed to load applications.');
      } finally {
        setApplicationsLoading(false);
      }
    };

    if (job) {
      fetchApplications();
    }
  }, [job_id, user, job]);

  const handleApplicationStatusChange = async (applicationId, newStatus) => {
    try {
      await axios.patch(`/jobs/applications/${applicationId}`, { status: newStatus });
      alert(`Application ${newStatus} successfully!`);
      setApplicationsLoading(true);
      setApplicationsError('');
      const response = await axios.get(`/jobs/${job_id}/applications`);
      setApplications(response.data);
      setApplicationsLoading(false);

      if (newStatus === 'accepted') {
        setLoading(true);
        setError('');
        const jobResponse = await axios.get(`/jobs/${job_id}`);
        setJob(jobResponse.data);
        setLoading(false);
      }

    } catch (err) {
      console.error(`Error updating application status to ${newStatus}:`, err);
      alert(`Failed to ${newStatus} application. ` + (err.response?.data?.detail || 'Please try again.'));
    }
  };

  const handleMarkAsComplete = async () => {
    try {
      await axios.put(`/jobs/${job_id}/complete`);
      alert('Job marked as complete!');
      setLoading(true);
      setError('');
      const jobResponse = await axios.get(`/jobs/${job_id}`);
      setJob(jobResponse.data);
      setLoading(false);
    } catch (err) {
      console.error('Error marking job as complete:', err);
      alert('Failed to mark job as complete. ' + (err.response?.data?.detail || 'Please try again.'));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Loading job details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-4">
        <p className="text-xl text-red-500 mb-4">{error}</p>
        <button
          onClick={() => navigate(-1)}
          className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-md transition duration-300"
        >
          Go Back
        </button>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-4">
        <p className="text-xl text-gray-700 mb-4">Job not found.</p>
        <button
          onClick={() => navigate(-1)}
          className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-md transition duration-300"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="relative flex size-full min-h-screen flex-col bg-white group/design-root overflow-x-hidden">
      <div className="layout-container flex h-full grow flex-col">
        <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-b-[#f5f1f0] px-10 py-3">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-4 text-[#181211] cursor-pointer" onClick={() => navigate('/home')}>
              <div className="size-4">
                <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <g clipPath="url(#clip0_6_543)">
                    <path
                      d="M42.1739 20.1739L27.8261 5.82609C29.1366 7.13663 28.3989 10.1876 26.2002 13.7654C24.8538 15.9564 22.9595 18.3449 20.6522 20.6522C18.3449 22.9595 15.9564 24.8538 13.7654 26.2002C10.1876 28.3989 7.13663 29.1366 5.82609 27.8261L20.1739 42.1739C21.4845 43.4845 24.5355 42.7467 28.1133 40.548C30.3042 39.2016 32.6927 37.3073 35 35C37.3073 32.6927 39.2016 30.3042 40.548 28.1133C42.7467 24.5355 43.4845 21.4845 42.1739 20.1739Z"
                      fill="currentColor"
                    ></path>
                    <path
                      fillRule="evenodd"
                      clipRule="evenodd"
                      d="M7.24189 26.4066C7.31369 26.4411 7.64204 26.5637 8.52504 26.3738C9.59462 26.1438 11.0343 25.5311 12.7183 24.4963C14.7583 23.2426 17.0256 21.4503 19.238 19.238C21.4503 17.0256 23.2426 14.7583 24.4963 12.7183C25.5311 11.0343 26.1438 9.59463 26.3738 8.52504C26.5637 7.64204 26.4411 7.31369 26.4066 7.24189C26.345 7.21246 26.143 7.14535 25.6664 7.1918C24.9745 7.25925 23.9954 7.5498 22.7699 8.14278C20.3369 9.32007 17.3369 11.4915 14.4142 14.4142C11.4915 17.3369 9.32007 20.3369 8.14278 22.7699C7.5498 23.9954 7.25925 24.9745 7.1918 25.6664C7.14534 26.143 7.21246 26.345 7.24189 26.4066ZM29.9001 10.7285C29.4519 12.0322 28.7617 13.4172 27.9042 14.8126C26.465 17.1544 24.4686 19.6641 22.0664 22.0664C19.6641 24.4686 17.1544 26.465 14.8126 27.9042C13.4172 28.7617 12.0322 29.4519 10.7285 29.9001L21.5754 40.747C21.6001 40.7606 21.8995 40.931 22.8729 40.7217C23.9424 40.4916 25.3821 39.879 27.0661 38.8441C29.1062 37.5904 31.3734 35.7982 33.5858 33.5858C35.7982 31.3734 37.5904 29.1062 38.8441 27.0661C39.879 25.3821 40.4916 23.9425 40.7216 22.8729C40.931 21.8995 40.7606 21.6001 40.747 21.5754L29.9001 10.7285ZM29.2403 4.41187L43.5881 18.7597C44.9757 20.1473 44.9743 22.1235 44.6322 23.7139C44.2714 25.3919 43.4158 27.2666 42.252 29.1604C40.8128 31.5022 38.8165 34.012 36.4142 36.4142C34.012 38.8165 31.5022 40.8128 29.1604 42.252C27.2666 43.4158 25.3919 44.2714 23.7139 44.6322C22.1235 44.9743 20.1473 44.9757 18.7597 43.5881L4.41187 29.2403C3.29027 28.1187 3.08209 26.5973 3.21067 25.2783C3.34099 23.9415 3.8369 22.4852 4.54214 21.0277C5.96129 18.0948 8.43335 14.7382 11.5858 11.5858C14.7382 8.43335 18.0948 5.9613 21.0277 4.54214C22.4852 3.8369 23.9415 3.34099 25.2783 3.21067C26.5973 3.08209 28.1187 3.29028 29.2403 4.41187Z"
                      fill="currentColor"
                    ></path>
                  </g>
                  <defs>
                    <clipPath id="clip0_6_543"><rect width="48" height="48" fill="white"></rect></clipPath>
                  </defs>
                </svg>
              </div>
              <h2 className="text-[#181211] text-lg font-bold leading-tight tracking-[-0.015em]">SkillConnect</h2>
            </div>
            <div className="flex items-center gap-9">
              <a className="text-[#181211] text-sm font-medium leading-normal" href="/services">Find Services</a>
              <a className="text-[#181211] text-sm font-medium leading-normal" href="/about">About Us</a>
              <a className="text-[#181211] text-sm font-medium leading-normal" href="/contact">Contact</a>
            </div>
          </div>
          <div className="flex flex-1 justify-end gap-8">
            {isAuthenticated ? (
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/profile')}
                  className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-[#f35120] text-white text-sm font-bold leading-normal tracking-[0.015em]"
                >
                  <span className="truncate">Profile</span>
                </button>
                <button
                  onClick={logout}
                  className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-[#f5f1f0] text-[#181211] text-sm font-bold leading-normal tracking-[0.015em]"
                >
                  <span className="truncate">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/register')}
                  className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-[#f35120] text-white text-sm font-bold leading-normal tracking-[0.015em]"
                >
                  <span className="truncate">Sign Up</span>
                </button>
                <button
                  onClick={() => navigate('/login')}
                  className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-[#f5f1f0] text-[#181211] text-sm font-bold leading-normal tracking-[0.015em]"
                >
                  <span className="truncate">Log In</span>
                </button>
              </div>
            )}
          </div>
        </header>
        <div className="px-40 flex flex-1 justify-center py-5">
          <div className="layout-content-container flex flex-col max-w-[960px] flex-1">
            <div className="flex flex-col gap-10 px-4 py-10 @container">
              <h1 className="text-3xl font-bold text-brand-text-primary mb-4">{job.title}</h1>
              <p className="text-brand-text-secondary mb-2"><strong>Location:</strong> {job.location}</p>
              <p className="text-brand-text-secondary mb-2"><strong>Budget:</strong> ${job.budget}</p>
              <p className="text-brand-text-secondary mb-2"><strong>Status:</strong> {job.status}</p>
              {job.required_skills && job.required_skills.length > 0 && (
                <p className="text-brand-text-secondary mb-2"><strong>Required Skills:</strong> {job.required_skills.join(', ')}</p>
              )}
              <p className="text-brand-text-secondary mb-4"><strong>Description:</strong> {job.description}</p>
              <p className="text-brand-text-secondary text-sm">Posted on: {new Date(job.created_at).toLocaleDateString()}</p>

              <div className="mt-6 flex space-x-4">
                <button
                  onClick={() => navigate(-1)}
                  className="bg-brand-primary hover:bg-orange-700 text-white font-bold py-2 px-4 rounded-md transition duration-300"
                >
                  Back to Listings
                </button>

                {user && user.user_type === 'artisan' && job.status === 'open' && (
                  <button
                    onClick={() => setShowApplyModal(true)}
                    className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-md transition duration-300"
                  >
                    Apply for Job
                  </button>
                )}

                {user && user.user_type === 'client' && job.client_id === user.id && job.status === 'assigned' && (
                  <button
                    onClick={handleMarkAsComplete}
                    className="bg-brand-primary hover:bg-orange-700 text-white font-bold py-2 px-4 rounded-md transition duration-300"
                  >
                    Mark as Complete
                  </button>
                )}

                {user && user.user_type === 'client' && job.client_id === user.id && job.status === 'completed' && !job.reviewed && (
                  <button
                    onClick={() => setShowReviewModal(true)}
                    className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded-md transition duration-300"
                  >
                    Leave Review
                  </button>
                )}
              </div>

              {user && user.user_type === 'client' && job.client_id === user.id && (
                <div className="mt-8">
                  <h2 className="text-2xl font-bold text-brand-text-primary mb-4">Job Applications</h2>
                  {applicationsLoading ? (
                    <p className="text-brand-text-secondary">Loading applications...</p>
                  ) : applicationsError ? (
                    <p className="text-red-500">{applicationsError}</p>
                  ) : applications.length === 0 ? (
                    <p className="text-brand-text-secondary">No applications for this job yet.</p>
                  ) : (
                    <ul className="space-y-4">
                      {applications.map((app) => (
                        <li key={app.id} className="bg-brand-secondary p-4 rounded-lg shadow-sm border border-brand-border">
                          <p className="text-lg font-semibold text-brand-text-primary">Artisan: {app.artisan.full_name}</p>
                          <p className="text-brand-text-secondary text-sm">Bid Amount: ${app.bid_amount}</p>
                          <p className="text-brand-text-secondary text-sm">Message: {app.message}</p>
                          <p className="text-brand-text-secondary text-xs">Status: {app.status} | Applied on: {new Date(app.created_at).toLocaleDateString()}</p>

                          {job.status === 'open' && app.status === 'pending' && (
                            <div className="mt-3 space-x-2">
                              <button
                                onClick={() => handleApplicationStatusChange(app.id, 'accepted')}
                                className="bg-green-500 hover:bg-green-600 text-white font-bold py-1 px-3 rounded-md text-sm transition duration-300"
                              >
                                Accept
                              </button>
                              <button
                                onClick={() => handleApplicationStatusChange(app.id, 'rejected')}
                                className="bg-red-500 hover:bg-red-600 text-white font-bold py-1 px-3 rounded-md text-sm transition duration-300"
                              >
                                Reject
                              </button>
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        <footer className="flex justify-center">
          <div className="flex max-w-[960px] flex-1 flex-col">
            <footer className="flex flex-col gap-6 px-5 py-10 text-center @container">
              <div className="flex flex-wrap items-center justify-center gap-6 @[480px]:flex-row @[480px]:justify-around">
                <a className="text-[#8a6a60] text-base font-normal leading-normal min-w-40" href="/terms">Terms of Service</a>
                <a className="text-[#8a6a60] text-base font-normal leading-normal min-w-40" href="/privacy">Privacy Policy</a>
                <a className="text-[#8a6a60] text-base font-normal leading-normal min-w-40" href="/contact">Contact Us</a>
              </div>
              <p className="text-[#8a6a60] text-base font-normal leading-normal"> @2024 SkillConnect. All rights reserved.</p>
            </footer>
          </div>
        </footer>
      </div>

      {showApplyModal && (
        <ApplyForJobForm
          jobId={job.id}
          onClose={() => setShowApplyModal(false)}
          onApplicationSuccess={() => {
            setShowApplyModal(false);
            alert('Application submitted successfully!');
            setLoading(true);
            setError('');
            setApplicationsLoading(true);
            setApplicationsError('');
            const fetchJobDetailsAndApplications = async () => {
              try {
                const jobResponse = await axios.get(`/jobs/${job_id}`);
                setJob(jobResponse.data);
                if (user && user.user_type === 'client' && user.id === jobResponse.data.client_id) {
                  const applicationsResponse = await axios.get(`/jobs/${job_id}/applications`);
                  setApplications(applicationsResponse.data);
                }
              } catch (err) {
                console.error('Error refreshing data after application:', err);
                setError('Failed to refresh job data.');
              } finally {
                setLoading(false);
                setApplicationsLoading(false);
              }
            };
            fetchJobDetailsAndApplications();
          }}
        />
      )}

      {console.log('Review Modal Conditional Check: showReviewModal=', showReviewModal, 'job.assigned_artisan_id=', job.assigned_artisan_id)}
      {showReviewModal && job.assigned_artisan_id && (
        <ReviewForm
          jobId={job.id}
          artisanId={job.assigned_artisan_id}
          onClose={() => setShowReviewModal(false)}
          onReviewSubmitted={() => {
            setShowReviewModal(false);
            alert('Review submitted successfully!');
            setLoading(true);
            setError('');
            const fetchJob = async () => {
              try {
                const response = await axios.get(`/jobs/${job_id}`);
                setJob(response.data);
              } catch (err) {
                console.error('Error refreshing job after review:', err);
                setError('Failed to refresh job data after review.');
              } finally {
                setLoading(false);
              }
            };
            fetchJob();
          }}
        />
      )}
    </div>
  );
}

export default JobDetailPage;
