import React from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Events from "./pages/Events";
import Dreams from "./pages/Dreams";
import Logs from "./pages/Logs";
import LiveChat from "./pages/LiveChat";
import { useAuth } from "./hooks/useAuth";

const App: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            isAuthenticated ? <Navigate to="/dashboard" /> : <Navigate to="/login" />
          }
        />
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />}
        />
        <Route
          path="/events"
          element={isAuthenticated ? <Events /> : <Navigate to="/login" />}
        />
        <Route
          path="/dreams"
          element={isAuthenticated ? <Dreams /> : <Navigate to="/login" />}
        />
        <Route
          path="/logs"
          element={isAuthenticated ? <Logs /> : <Navigate to="/login" />}
        />
        <Route
          path="/chat"
          element={isAuthenticated ? <LiveChat /> : <Navigate to="/login" />}
        />
      </Routes>
    </Router>
  );
};

export default App;
