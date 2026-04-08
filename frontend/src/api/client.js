import axios from 'axios';

const http = axios.create({ baseURL: '/api' });

export const matchesApi = {
  listScenarios: () => http.get('/matches/scenarios').then(r => r.data),
  getScenario: name => http.get(`/matches/scenarios/${name}`).then(r => r.data),
  listLive: (refresh = false) =>
    http.get('/matches/live', { params: { refresh } }).then(r => r.data),
  getLiveState: (ref = null, refresh = false) =>
    http.get('/matches/live/state', { params: { ref, refresh } }).then(r => r.data),
};

export const analysisApi = {
  runAnalysis: state => http.post('/analysis/', state).then(r => r.data),
};

export const historyApi = {
  getHistory: (matchKey, limit = 50) =>
    http.get(`/history/${matchKey}`, { params: { limit } }).then(r => r.data),
};
