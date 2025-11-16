import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { datadogRum } from '@datadog/browser-rum';
import { datadogLogs } from '@datadog/browser-logs';

// Datadog RUM 初期化
if (process.env.REACT_APP_DD_RUM_APPLICATION_ID && process.env.REACT_APP_DD_RUM_CLIENT_TOKEN) {
  datadogRum.init({
    applicationId: process.env.REACT_APP_DD_RUM_APPLICATION_ID,
    clientToken: process.env.REACT_APP_DD_RUM_CLIENT_TOKEN,
    site: process.env.REACT_APP_DD_RUM_SITE || 'datadoghq.com',
    service: process.env.REACT_APP_DD_RUM_SERVICE || 'frontend',
    env: process.env.REACT_APP_DD_RUM_ENV || 'dev',
    version: '1.0.0',
    sessionSampleRate: 100,
    sessionReplaySampleRate: 100,
    trackUserInteractions: true,
    trackResources: true,
    trackLongTasks: true,
    defaultPrivacyLevel: 'mask-user-input',
  });

  // Datadog Logs 初期化
  datadogLogs.init({
    clientToken: process.env.REACT_APP_DD_RUM_CLIENT_TOKEN,
    site: process.env.REACT_APP_DD_RUM_SITE || 'datadoghq.com',
    service: process.env.REACT_APP_DD_RUM_SERVICE || 'frontend',
    env: process.env.REACT_APP_DD_RUM_ENV || 'dev',
    forwardErrorsToLogs: true,
    sessionSampleRate: 100,
  });

  console.log('Datadog RUM initialized successfully');
} else {
  console.warn('Datadog RUM not initialized: Missing APPLICATION_ID or CLIENT_TOKEN');
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
