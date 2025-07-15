import axios from './axios';

export const getArtisans = (skills) => axios.get(`/artisans?skills=${skills}`);
export const getArtisanById = (id) => axios.get(`/artisans/${id}`);
