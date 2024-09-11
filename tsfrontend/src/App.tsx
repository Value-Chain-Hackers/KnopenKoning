import React, { useState } from "react";

import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import Header from "./Header";
import QuestionPage from "./pages/QuestionPage";
import AdminPage from "./pages/AdminPage";
import StartPage from "./pages/StartPage";
import Login from "./components/Login";
import Register from "./components/Register";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import "./App.css";
import { SettingsProvider } from "./contexts/SettingsContext";

const AppRoutes = () => {
  const { isAuthenticated, isAdmin, isLoading } = useAuth();
  const [question, setQuestion] = useState("");

  const handleStarterClick = (message: string) => {
    console.log("Starter clicked:", message);
    setQuestion(message);
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <SettingsProvider>
      <AuthProvider>
        <div className={`app-container`}>
          <div className="main-content">
            <Header title="ChainWise" />
            <div className="App">
              <Routes>
                <Route
                  path="/login"
                  element={!isAuthenticated ? <Login /> : <Navigate to="/" />}
                />
                <Route
                  path="/register"
                  element={
                    !isAuthenticated ? <Register /> : <Navigate to="/" />
                  }
                />
                <Route
                  path="/"
                  element={
                    isAuthenticated ? (
                      <StartPage
                        onStarterClick={handleStarterClick}
                        question={question}
                        setQuestion={setQuestion}
                      />
                    ) : (
                      <Navigate to="/login" />
                    )
                  }
                />
                <Route
                  path="/view/:uid"
                  element={
                    isAuthenticated ? (
                      <QuestionPage />
                    ) : (
                      <Navigate to="/login" />
                    )
                  }
                />
                <Route
                  path="/view/:uid/followup/:qq"
                  element={
                    isAuthenticated ? (
                      <QuestionPage followup={true} />
                    ) : (
                      <Navigate to="/login" />
                    )
                  }
                />
                <Route
                  path="/admin"
                  element={
                    isAuthenticated && isAdmin ? (
                      <AdminPage />
                    ) : (
                      <Navigate to="/" />
                    )
                  }
                />
              </Routes>
            </div>
          </div>
          <footer className="footer" id="footer">
            <span>Status: Ready</span>
          </footer>
        </div>
      </AuthProvider>
    </SettingsProvider>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
};

export default App;
