import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import AOS from 'aos'
import 'aos/dist/aos.css'

import { PipelineProvider } from './context/PipelineContext'
import Layout from './components/Layout'
import LandingPage from './pages/LandingPage'
import AppPage from './pages/AppPage'
import HistoryPage from './pages/HistoryPage'

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
          <Route path="/app" element={<AppPage />} />
          <Route path="/history" element={<HistoryPage />} />
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
