import { useState } from 'react'
import { Layout } from 'antd'
import ApiKeySetup from './components/ApiKeySetup'
import JobAnalysis from './components/JobAnalysis'
import ResumeUpload from './components/ResumeUpload'
import Optimization from './components/Optimization'
import Preview from './components/Preview'
import StepsProgress from './components/StepsProgress'
import useResumeStore from './store/resumeStore'
import ErrorBoundary from './components/ErrorBoundary'

const { Content } = Layout

const App = () => {
  const { currentStep, setCurrentStep } = useResumeStore()
  
  const handleStepComplete = (nextStep) => {
    setCurrentStep(nextStep)
  }

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <ApiKeySetup onComplete={() => handleStepComplete(1)} />
      case 1:
        return <ResumeUpload 
          onComplete={() => handleStepComplete(2)} 
          onBack={() => handleStepComplete(0)} 
        />
      case 2:
        return <JobAnalysis 
          onComplete={() => handleStepComplete(3)} 
          onBack={() => handleStepComplete(1)} 
        />
      case 3:
        return <Optimization 
          onComplete={() => handleStepComplete(4)} 
          onBack={() => handleStepComplete(2)} 
        />
      case 4:
        return <Preview onBack={() => handleStepComplete(3)} />
      default:
        return null
    }
  }

  return (
    <ErrorBoundary>
      <Layout className="min-h-screen bg-gray-50">
        <Content className="p-6">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-3xl font-bold text-center mb-8">
              Resume ATS Optimizer
            </h1>
            
            <StepsProgress currentStep={currentStep} />
            
            <div className="bg-white rounded-lg shadow-sm p-6">
              {renderStep()}
            </div>
          </div>
        </Content>
      </Layout>
    </ErrorBoundary>
  )
}

export default App
