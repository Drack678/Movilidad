import { Switch, Route, Router } from "wouter";
import { useHashLocation } from "wouter/use-hash-location";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import NotFound from "@/pages/not-found";
import PlannerPage from "@/pages/planner";
import ComparePage from "@/pages/compare";
import TrafficPage from "@/pages/traffic";
import AcoVizPage from "@/pages/aco-viz";
import AnalyticsPage from "@/pages/analytics";
import LocationsPage from "@/pages/locations";

function AppRouter() {
  return (
    <Switch>
      <Route path="/" component={PlannerPage} />
      <Route path="/comparar" component={ComparePage} />
      <Route path="/trafico" component={TrafficPage} />
      <Route path="/aco" component={AcoVizPage} />
      <Route path="/analitica" component={AnalyticsPage} />
      <Route path="/ubicaciones" component={LocationsPage} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <Toaster />
          <Router hook={useHashLocation}>
            <AppRouter />
          </Router>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
