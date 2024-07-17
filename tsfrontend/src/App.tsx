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

  const handleSubmit = async (questionText: string) => {
    try {
      const response = await fetch('http://localhost:18000/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          company: 'Danone',
          question: questionText,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit question');
      }

      const data = await response.json();
      window.location.href = `/view/${data.uid}`; // Navigate to the question page
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleStarterClick = (message: string) => {
    setQuestion(message);
  };

  return (
    <Router>
      <div className={`app-container ${isChatOpen ? 'chat-open' : ''}`}>
        <div className="main-content">
          <Header title="ChainWise" />
          <div className="App">
            <Routes>
              <Route path="/" element={<StartPage onSubmit={handleSubmit} onStarterClick={handleStarterClick} question={question} setQuestion={setQuestion} />} />
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
