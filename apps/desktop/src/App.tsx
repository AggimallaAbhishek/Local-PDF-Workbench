import { useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { JobHistory } from "./pages/JobHistory";
import { ToolWorkspace } from "./pages/ToolWorkspace";

function App() {
  const [openToolId, setOpenToolId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  if (openToolId) {
    return <ToolWorkspace toolId={openToolId} onBack={() => setOpenToolId(null)} />;
  }

  if (showHistory) {
    return <JobHistory onBack={() => setShowHistory(false)} />;
  }

  return <Dashboard onSelectTool={(tool) => setOpenToolId(tool.id)} onOpenHistory={() => setShowHistory(true)} />;
}

export default App;
