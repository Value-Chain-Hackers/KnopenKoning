import React, { useEffect, useState } from "react";
import { useParams, Navigate } from "react-router-dom";
import axios from "axios";
import TabControl from "../components/TabControl";
import { useAuth } from "../contexts/AuthContext";
import ChatDialog from "../components/ChatDialog";
import ChatButton from "../components/ChatButton";

interface QuestionPageProps {
  followup?: boolean;
}

const QuestionPage: React.FC<QuestionPageProps> = ({followup}) => {
  const { uid, qq } = useParams<{ uid: string, qq:string }>();
  const [question, setQuestion] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated, isLoading } = useAuth();
  const [isChatOpen, setIsChatOpen] = useState(false);
  const fetchQuestion = async () => {
    console.log("fetching question", uid, qq);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/view/${uid}/` + (followup ? "`followup/"+ qq : ""), {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setQuestion(response.json());     
    } catch (error) {
      console.error("Error fetching question:", error);
      setError("Failed to fetch question data");
    }
  };

  useEffect(() => {
    if (isAuthenticated && uid) {
      fetchQuestion();
    }
  }, [isAuthenticated, uid]);

  
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
      <a href={`${process.env.REACT_APP_BACKEND_URL}/view/` + uid+'/pdf'} target="_blank" rel="noreferrer">As PDF</a>
      <TabControl url={`${process.env.REACT_APP_BACKEND_URL}/view`} sessionId={uid} />
      <ChatDialog isOpen={isChatOpen} sessionId={uid} onClose={() => setIsChatOpen(false)} />
      {!isChatOpen && <ChatButton onClick={() => setIsChatOpen(true)} />}
    </div>
  );
};

export default QuestionPage;
