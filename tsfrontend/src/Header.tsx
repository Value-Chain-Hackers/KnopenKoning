import React from "react";
import { useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCog, faSignOutAlt } from "@fortawesome/free-solid-svg-icons";
import "./Header.css";

interface HeaderProps {
  title: string;
}

const Header: React.FC<HeaderProps> = ({ title }) => {
  const navigate = useNavigate();

  const handleAdminClick = () => {
    navigate('/admin');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="header">
      <div className="avatar">
        <a href="/">
          <img src="/profile.webp" className="avatar" alt="Profile" />
        </a>
      </div>
      <div className="titleBar">{title}</div>
      <button id="adminButton" className="admin-button" style={{ backgroundColor: "transparent" }} onClick={handleAdminClick}>
        <FontAwesomeIcon icon={faCog} size="lg" />
      </button>
      <button id="logoutButton" className="logout-button" style={{ backgroundColor: "transparent" }} onClick={handleLogout}>
        <FontAwesomeIcon icon={faSignOutAlt} size="lg" />
      </button>
    </div>
  );
};

export default Header;