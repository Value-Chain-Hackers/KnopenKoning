import React, { useEffect, useState } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import axios from 'axios';
import TabControl from '../components/TabControl';
import { useAuth } from '../contexts/AuthContext';

const QuestionPage: React.FC = () => {
  const { uid } = useParams<{ uid: string }>();
  const [question, setQuestion] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (isAuthenticated && uid) {
      fetchQuestion();
    }
  }, [isAuthenticated, uid]);

  const fetchQuestion = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`http://localhost:18000/view/${uid}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setQuestion(response.data);
    } catch (error) {
      console.error('Error fetching question:', error);
      setError('Failed to fetch question data');
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
    <TabControl url='http://localhost:18000/view/' sessionId={uid} />
  );
};

export default QuestionPage;