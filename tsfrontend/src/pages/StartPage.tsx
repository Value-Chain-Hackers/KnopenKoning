import React from "react";
import {
  faDollarSign,
  faGlobe,
  faRocket,
  faTruck,
} from "@fortawesome/free-solid-svg-icons";
import StarterCard from "../components/StarterCard";

interface StartPageProps {
  onSubmit: (question: string) => Promise<void>;
  onStarterClick: (message: string) => void;
  question: string;
  setQuestion: React.Dispatch<React.SetStateAction<string>>;
}

const StartPage: React.FC<StartPageProps> = ({
  onSubmit,
  onStarterClick,
  question,
  setQuestion,
}) => {
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    await onSubmit(question);
  };

  return (
    <div className="form-container">
      <form onSubmit={handleSubmit}>
        <div style={{ display: "block", width:"100%" }}>
            <br/><br/>
          <h2 className="mb-4">Ask a Question</h2>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question here"
            required
          />
          <div className=" gap-4">
            <button type="submit">Submit</button>
          </div>
        </div>
      </form>
      <div className="starter-proposals grid grid-cols-1 md:grid-cols-2 gap-4">
        <StarterCard
          icon={faDollarSign}
          text="What are the latest funding rounds in the AI industry?"
          onClick={onStarterClick}
        />
        <StarterCard
          text="Who are the suppliers of Unilever ?"
          icon={faTruck}
          onClick={onStarterClick}
        />
        <StarterCard
          icon={faGlobe}
          text="What are the latest AI trends in the automotive industry?"
          onClick={onStarterClick}
        />
        <StarterCard
          icon={faRocket}
          text="What are the latest AI trends in the finance industry?"
          onClick={onStarterClick}
        />
      </div>
    </div>
  );
};

export default StartPage;
