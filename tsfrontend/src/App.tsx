import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ChatButton from './components/ChatButton';
import ChatDialog from './components/ChatDialog';
import Header from './Header';
import QuestionPage from './pages/QuestionPage';
import AdminPage from './pages/AdminPage';
import StartPage from './pages/StartPage';
import './App.css';

const App: React.FC = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleStarterClick = (message: string) => {
    console.log('Starter clicked:', message);
    setQuestion(message);
  };

  return (
    <Router>
      <div className={`app-container ${isChatOpen ? 'chat-open' : ''}`}>
        <div className="main-content">
          <Header title="ChainWise" />
          <div className="App">
            <Routes>
              <Route path="/" element={<StartPage onStarterClick={handleStarterClick} question={question} setQuestion={setQuestion} />} />
              <Route path="/view/:uid" element={<QuestionPage />} />
              <Route path="/admin" element={<AdminPage />} />
            </Routes>
          </div>
        </div>
        <ChatDialog isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
        {!isChatOpen && <ChatButton onClick={() => setIsChatOpen(true)} />}
        <footer className="footer" id="footer">
          <span>Status: Ready</span>
        </footer>
      </div>
    </Router>
  );
};

export default App;
