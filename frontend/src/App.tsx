import { useState } from 'react';
import { Layout } from './components/Layout';
import { ChatInterface } from './components/ChatInterface';

function App() {
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [metrics, setMetrics] = useState({ totalTokens: 0, totalCost: 0, totalCarbon: 0 });

  return (
    <Layout
      currentSessionId={sessionId}
      onSessionSelect={setSessionId}
      onNewChat={() => {
        setSessionId(undefined);
        setMetrics({ totalTokens: 0, totalCost: 0, totalCarbon: 0 });
      }}
      metrics={metrics}
    >
      <ChatInterface
        sessionId={sessionId}
        onSessionCreate={setSessionId}
        onMetricsUpdate={setMetrics}
      />
    </Layout>
  );
}

export default App;
