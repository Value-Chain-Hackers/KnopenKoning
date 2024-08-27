import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import Graph from '../components/Graph';
import TabControl from '../components/TabControl';

interface Question {
  uid: string;
  company: string;
  question: string;
  // Add other fields as necessary
}

const QuestionPage: React.FC = () => {
  const { uid } = useParams<{ uid: string }>();
  const [question, setQuestion] = useState<Question | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {

  }, [uid]);

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <TabControl url='http://localhost:18000/view/' sessionId={uid} />
  );
};

export default QuestionPage;
