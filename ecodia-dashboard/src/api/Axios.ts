// src/api/axios.ts
import axios from "axios";

const API_BASE = "http://localhost:5001/api";

export const getToken = () => localStorage.getItem("token");

const instance = axios.create({
  baseURL: API_BASE,
});

instance.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default instance;
