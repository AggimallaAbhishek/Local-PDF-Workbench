import { useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { ToolWorkspace } from "./pages/ToolWorkspace";

function App() {
  const [openToolId, setOpenToolId] = useState<string | null>(null);

  if (openToolId) {
    return <ToolWorkspace toolId={openToolId} onBack={() => setOpenToolId(null)} />;
  }

  return <Dashboard onSelectTool={(tool) => setOpenToolId(tool.id)} />;
}

export default App;
