import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import AOS from 'aos'
import 'aos/dist/aos.css'

import { PipelineProvider } from './context/PipelineContext'
import Layout from './components/Layout'
import PrivateRoute from './components/PrivateRoute'
import LandingPage from './pages/LandingPage'
import AppPage from './pages/AppPage'
import HistoryPage from './pages/HistoryPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

export default function App() {
  useEffect(() => {
    AOS.init({
      duration: 700,
      easing: 'ease-out-cubic',
      once: true,
      offset: 80,
    })
  }, [])

  return (
    <>
      <Routes>
        <Route
          element={
            <PipelineProvider>
              <Layout />
            </PipelineProvider>
          }
        >
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/app"
            element={
              <PrivateRoute>
                <AppPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/history"
            element={
              <PrivateRoute>
                <HistoryPage />
              </PrivateRoute>
            }
          />
        </Route>
      </Routes>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            fontFamily: 'Inter, sans-serif',
            fontSize: '14px',
            borderRadius: '0px',
            border: '1px solid #000',
          },
        }}
      />
    </>
  )
}
