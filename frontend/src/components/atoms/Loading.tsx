/**
 * Loading Spinner Component - Presentational
 */

import './Loading.css';

export const Loading = () => {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>로딩 중...</p>
    </div>
  );
};
