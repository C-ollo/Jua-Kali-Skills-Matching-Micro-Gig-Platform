// frontend/src/pages/DashboardPage.jsx
import React, { useState, useEffect } from 'react';
import axios from '../api/axios';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import PostJobForm from '../components/PostJobForm';
import ArtisanServices from '../components/ArtisanServices';

// Simple ClientJobManagement component
const ClientJobManagement = () => {
  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <p className="text-gray-700 mb-3">Manage jobs you've posted, view applications, and track progress.</p>
      <button className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-md transition duration-300">
        View My Jobs
      </button>
    </div>
  );
};

function DashboardPage() {
  const [showPostJobModal, setShowPostJobModal] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [jobsError, setJobsError] = useState('');
  
  // Filter state variables
  const [filterLocation, setFilterLocation] = useState('');
  const [filterSkills, setFilterSkills] = useState('');
  const [filterMinBudget, setFilterMinBudget] = useState('');
  const [filterMaxBudget, setFilterMaxBudget] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  
  const { user, logout, loading, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Show loading state if authentication context is still loading
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <p className="text-xl text-gray-700">Loading dashboard...</p>
      </div>
    );
  }

  // If for some reason user is null but not loading (e.g., direct access without token)
  if (!user) {
    navigate('/login'); // Redirect to login if not authenticated
    return null; // Don't render anything
  }

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await axios.get('/jobs/');
        setJobs(response.data.jobs); // Assuming the API returns { jobs: [], total_count: ... }
      } catch (err) {
        console.error('Error fetching jobs:', err);
        setJobsError('Failed to load jobs.');
      } finally {
        setJobsLoading(false);
      }
    };

    fetchJobs();
  }, []);

  // Filter jobs based on filter criteria
  const filteredJobs = jobs.filter(job => {
    const matchesLocation = !filterLocation || job.location.toLowerCase().includes(filterLocation.toLowerCase());
    const matchesSkills = !filterSkills || (job.required_skills && job.required_skills.some(skill => 
      filterSkills.split(',').some(filterSkill => 
        skill.toLowerCase().includes(filterSkill.trim().toLowerCase())
      )
    ));
    const matchesMinBudget = !filterMinBudget || job.budget >= parseFloat(filterMinBudget);
    const matchesMaxBudget = !filterMaxBudget || job.budget <= parseFloat(filterMaxBudget);
    const matchesStatus = !filterStatus || job.status === filterStatus;
    
    return matchesLocation && matchesSkills && matchesMinBudget && matchesMaxBudget && matchesStatus;
  });

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
              <h1 className="text-[#181211] tracking-light text-[32px] font-bold leading-tight @[480px]:text-4xl @[480px]:font-black @[480px]:leading-tight @[480px]:tracking-[-0.033em] max-w-[720px]">
                Welcome to Your Dashboard, {user.full_name}!
              </h1>

              <div className="mb-8">
                <p className="text-[#181211] text-base font-normal leading-normal">This is your central hub for managing your Juakali activities.</p>
                <p className="text-[#8a6a60] text-sm font-normal leading-normal mt-2">
                  You are logged in as a <span className="font-semibold text-brand-primary capitalize">{user.user_type}</span>.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-brand-secondary p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                  <h2 className="text-xl font-semibold text-brand-text-primary mb-2">My Profile</h2>
                  <p className="text-brand-text-secondary mb-3">View and update your personal details and {user.user_type === 'artisan' ? 'artisan information and skills.' : 'contact information.'}</p>
                  <button
                    onClick={() => navigate('/profile')}
                    className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-brand-primary text-white text-sm font-bold leading-normal tracking-[0.015em]"
                  >
                    <span className="truncate">Go to Profile</span>
                  </button>
                </div>

                {user.user_type === 'client' && (
                  <div className="bg-brand-secondary p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow col-span-full">
                    <h2 className="text-xl font-semibold text-brand-text-primary mb-2">Manage My Posted Jobs</h2>
                    <ClientJobManagement />
                  </div>
                )}

                {user.user_type === 'artisan' && (
                  <div className="bg-brand-secondary p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow col-span-full">
                    <h2 className="text-xl font-semibold text-brand-text-primary mb-2">Manage My Services</h2>
                    <ArtisanServices />
                  </div>
                )}

                <div className="bg-brand-secondary p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow col-span-full">
                  <h2 className="text-xl font-semibold text-brand-text-primary mb-2">Available Job Listings</h2>

                  <div className="mb-6 p-4 bg-white rounded-lg shadow-inner">
                    <h3 className="text-lg font-semibold text-brand-text-primary mb-3">Filter Jobs</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div>
                        <label htmlFor="filterLocation" className="block text-sm font-medium text-brand-text-secondary">Location</label>
                        <input
                          type="text"
                          id="filterLocation"
                          className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                          value={filterLocation}
                          onChange={(e) => setFilterLocation(e.target.value)}
                          placeholder="e.g., Nairobi"
                        />
                      </div>
                      <div>
                        <label htmlFor="filterSkills" className="block text-sm font-medium text-brand-text-secondary">Skills (comma-separated)</label>
                        <input
                          type="text"
                          id="filterSkills"
                          className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                          value={filterSkills}
                          onChange={(e) => setFilterSkills(e.target.value)}
                          placeholder="e.g., Plumbing,Carpentry"
                        />
                      </div>
                      <div>
                        <label htmlFor="filterMinBudget" className="block text-sm font-medium text-brand-text-secondary">Min Budget</label>
                        <input
                          type="number"
                          id="filterMinBudget"
                          step="0.01"
                          className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                          value={filterMinBudget}
                          onChange={(e) => setFilterMinBudget(e.target.value)}
                          placeholder="e.g., 100"
                        />
                      </div>
                      <div>
                        <label htmlFor="filterMaxBudget" className="block text-sm font-medium text-brand-text-secondary">Max Budget</label>
                        <input
                          type="number"
                          id="filterMaxBudget"
                          step="0.01"
                          className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                          value={filterMaxBudget}
                          onChange={(e) => setFilterMaxBudget(e.target.value)}
                          placeholder="e.g., 1000"
                        />
                      </div>
                      <div>
                        <label htmlFor="filterStatus" className="block text-sm font-medium text-brand-text-secondary">Status</label>
                        <select
                          id="filterStatus"
                          className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
                          value={filterStatus}
                          onChange={(e) => setFilterStatus(e.target.value)}
                        >
                          <option value="">All</option>
                          <option value="open">Open</option>
                          <option value="assigned">Assigned</option>
                          <option value="completed">Completed</option>
                          <option value="cancelled">Cancelled</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {jobsLoading ? (
                    <p className="text-brand-text-secondary">Loading jobs...</p>
                  ) : jobsError ? (
                    <p className="text-red-500">Error loading jobs: {jobsError}</p>
                  ) : filteredJobs.length === 0 ? (
                    <p className="text-brand-text-secondary">No jobs match your current filters.</p>
                  ) : (
                    <ul className="space-y-3">
                      {filteredJobs.map((job) => (
                        <li key={job.id} className="bg-white p-3 rounded-md shadow-sm border border-brand-border cursor-pointer hover:bg-gray-50">
                          <Link to={`/jobs/${job.id}`} className="block">
                            <h3 className="text-lg font-semibold text-brand-text-primary">{job.title}</h3>
                            <p className="text-brand-text-secondary text-sm">{job.description}</p>
                            <p className="text-brand-text-secondary text-xs">Location: {job.location} | Budget: ${job.budget} | Status: {job.status}</p>
                            {job.required_skills && job.required_skills.length > 0 && (
                              <p className="text-brand-text-secondary text-xs">Skills: {job.required_skills.join(', ')}</p>
                            )}
                          </Link>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              <div className="mt-8 text-center">
                <button
                  onClick={logout}
                  className="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-red-500 text-white text-sm font-bold leading-normal tracking-[0.015em]"
                >
                  <span className="truncate">Logout</span>
                </button>
              </div>

              {showPostJobModal && (
                <PostJobForm
                  onClose={() => setShowPostJobModal(false)}
                  onJobPosted={(newJob) => {
                    console.log('Job posted:', newJob);
                    setShowPostJobModal(false);
                    // Optionally, you can add logic here to update a list of jobs on the dashboard
                  }}
                />
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
    </div>
  );
}

export default DashboardPage;