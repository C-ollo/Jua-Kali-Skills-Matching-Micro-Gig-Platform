import React, { useState, useEffect } from 'react';
import axios from '../api/axios';
import Select from 'react-select';

function EditJobForm({ job, onClose, onJobUpdated }) {
  const [title, setTitle] = useState(job.title);
  const [description, setDescription] = useState(job.description);
  const [location, setLocation] = useState(job.location);
  const [budget, setBudget] = useState(job.budget);
  const [status, setStatus] = useState(job.status);
  const [skills, setSkills] = useState([]);
  const [selectedSkills, setSelectedSkills] = useState(
    job.required_skills ? job.required_skills.map(s => ({ value: s, label: s })) : []
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const response = await axios.get('/skills/');
        setSkills(response.data.map(skill => ({ value: skill.name, label: skill.name })));
      } catch (err) {
        console.error('Error fetching skills:', err);
        setError('Failed to load skills. Please try again.');
      }
    };
    fetchSkills();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const jobData = {
        title,
        description,
        location,
        budget: parseFloat(budget),
        status,
        required_skills: selectedSkills.map(skill => skill.value),
      };
      
      await axios.put(`/jobs/${job.id}`, jobData);
      setSuccess('Job updated successfully!');
      onJobUpdated();
    } catch (err) {
      console.error('Error updating job:', err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to update job. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex justify-center items-center">
      <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full">
        <h2 className="text-2xl font-bold text-brand-text-primary mb-6">Edit Job: {job.title}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-brand-text-secondary">Job Title</label>
            <input
              type="text"
              id="title"
              className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-brand-text-secondary">Description</label>
            <textarea
              id="description"
              rows="4"
              className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
            ></textarea>
          </div>
          <div>
            <label htmlFor="location" className="block text-sm font-medium text-brand-text-secondary">Location</label>
            <input
              type="text"
              id="location"
              className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="budget" className="block text-sm font-medium text-brand-text-secondary">Budget ($)</label>
            <input
              type="number"
              id="budget"
              step="0.01"
              className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-brand-text-secondary">Status</label>
            <select
              id="status"
              className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-md shadow-sm focus:outline-none focus:ring-brand-primary focus:border-brand-primary"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="open">Open</option>
              <option value="assigned">Assigned</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <label htmlFor="skills" className="block text-sm font-medium text-brand-text-secondary">Required Skills</label>
            <Select
              id="skills"
              isMulti
              options={skills}
              className="basic-multi-select mt-1"
              classNamePrefix="select"
              onChange={setSelectedSkills}
              value={selectedSkills}
              isLoading={skills.length === 0}
              placeholder="Select skills..."
            />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}
          {success && <p className="text-green-500 text-sm">{success}</p>}

          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-brand-border rounded-md text-brand-text-secondary hover:bg-brand-secondary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-primary"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-brand-primary text-white rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-primary disabled:opacity-50"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default EditJobForm;
