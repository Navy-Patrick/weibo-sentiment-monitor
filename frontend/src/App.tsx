import React from 'react'
import { Routes, Route } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import DataCollection from './pages/DataCollection'
import Posts from './pages/Posts'
import Comments from './pages/Comments'
import Alerts from './pages/Alerts'
import Settings from './pages/Settings'
import AITemplate from './pages/AITemplate'

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="collection" element={<DataCollection />} />
        <Route path="posts" element={<Posts />} />
        <Route path="posts/:postId/comments" element={<Comments />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="ai-template" element={<AITemplate />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App