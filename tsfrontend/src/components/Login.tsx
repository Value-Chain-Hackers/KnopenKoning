import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/auth/login`, {
        username,
        password
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.data && response.data.token) {
        await login(response.data.token);
        console.log('logged as user')
        window.location.assign("/")
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Failed to login. Please check your credentials.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="px-8 py-6 mt-4 text-left bg-gray-800 shadow-lg rounded-lg">
        <h3 className="text-2xl font-bold text-center text-white">Login to your account</h3>
        <form onSubmit={handleLogin}>
          <div className="mt-4">
            <div>
              <label className="block text-gray-300" htmlFor="username">Username</label>
              <input
                type="text"
                placeholder="Enter Username"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 mt-2 bg-gray-700 text-white border border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                required
              />
            </div>
            <div className="mt-4">
              <label className="block text-gray-300" htmlFor="password">Password</label>
              <input
                type="password"
                placeholder="Enter Password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 mt-2 bg-gray-700 text-white border border-gray-600 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                required
              />
            </div>
            <div className="flex items-center justify-between mt-4">
              <button
                type="submit"
                className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors duration-300"
              >
                Login
              </button>
            </div>
            <a href="/register" className="block mt-4 text-center text-blue-400 hover:text-blue-500">Create an account</a>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;