import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatPage } from "./pages/ChatPage";
import { DashboardPage } from "./pages/DashboardPage";
import { SettingsPage } from "./pages/SettingsPage";
import type { ViewKey } from "./types";

function App() {
  const [activeView, setActiveView] = useState<ViewKey>("chat");

  return (
    <div className="min-h-screen bg-transparent p-4 text-ink md:p-6">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-[1600px] gap-4 lg:h-[calc(100vh-3rem)] lg:min-h-0 lg:grid-cols-[280px_1fr]">
        <Sidebar activeView={activeView} onChangeView={setActiveView} />

        <main className="min-h-[70vh] lg:min-h-0">
          {activeView === "chat" ? <ChatPage /> : null}
          {activeView === "dashboard" ? <DashboardPage /> : null}
          {activeView === "settings" ? <SettingsPage /> : null}
        </main>
      </div>
    </div>
  );
}

export default App;
