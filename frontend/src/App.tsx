import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import GenerateRFQ from "./pages/GenerateRFQ";
import MyRFQs from "./pages/MyRFQs";
import DocumentLibrary from "./pages/DocumentLibrary";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import ProtectedRoute from "./components/ProtectedRoute";
import { useEffect } from "react";
import { getConfig } from "./api";

const queryClient = new QueryClient();

const App = () => {
  // Validate Server Instance on Mount/Reload
  useEffect(() => {
    const checkInstance = async () => {
      const token = localStorage.getItem("token");
      if (!token) return;

      try {
        const config = await getConfig();
        const storedInstanceId = localStorage.getItem("server_instance_id");

        if (storedInstanceId && config.instanceId && storedInstanceId !== config.instanceId) {
          console.warn("Server restarted. Invalidating session.");
          localStorage.clear();
          window.location.href = "/login";
        } else if (!storedInstanceId && config.instanceId) {
          // If we have a token but no instance ID (legacy session), update it or force logout. 
          // Let's force logout to be safe and consistent.
          localStorage.clear();
          window.location.href = "/login";
        }
      } catch (e) {
        console.error("Failed to validate server instance", e);
      }
    };

    checkInstance();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Index />
                </ProtectedRoute>
              }
            />
            <Route
              path="/generate"
              element={
                <ProtectedRoute>
                  <GenerateRFQ />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rfqs"
              element={
                <ProtectedRoute>
                  <MyRFQs />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rfqs/:id"
              element={
                <ProtectedRoute>
                  <MyRFQs />
                </ProtectedRoute>
              }
            />
            <Route
              path="/library"
              element={
                <ProtectedRoute>
                  <DocumentLibrary />
                </ProtectedRoute>
              }
            />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
