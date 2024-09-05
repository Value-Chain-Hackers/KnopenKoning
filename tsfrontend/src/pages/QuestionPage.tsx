import React, { useEffect, useState } from "react";
import { useParams, Navigate } from "react-router-dom";
import axios from "axios";
import TabControl from "../components/TabControl";
import { useAuth } from "../contexts/AuthContext";
import { useSettings } from "../contexts/SettingsContext";
import ChatDialog from "../components/ChatDialog";
import ChatButton from "../components/ChatButton";

const QuestionPage: React.FC = () => {
  const settings = useSettings();
  const { uid } = useParams<{ uid: string }>();
  const [question, setQuestion] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated, isLoading } = useAuth();
  const [isChatOpen, setIsChatOpen] = useState(false);
  
  useEffect(() => {
    if (isAuthenticated && uid) {
      fetchQuestion();
    }
  }, [isAuthenticated, uid]);

  const fetchQuestion = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${settings.apiUrl}/view/${uid}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setQuestion(response.data);
    } catch (error) {
      console.error("Error fetching question:", error);
      setError("Failed to fetch question data");
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!question) {
    return <div>Loading question data...</div>;
  }

  return (
    <div>
      <a href={settings.apiUrl + '/view/' + uid+'/pdf'} target="_blank" rel="noreferrer">As PDF</a>
      <TabControl url={settings.apiUrl + '/view'} sessionId={uid} />
      <ChatDialog isOpen={isChatOpen} sessionId={uid} onClose={() => setIsChatOpen(false)} />
      {!isChatOpen && <ChatButton onClick={() => setIsChatOpen(true)} />}
    </div>
  );
};

export default QuestionPage;
