import { Component, type ErrorInfo, type ReactNode } from "react";

interface State { error: Error | null }

/**
 * Last line of defence: without it, any render error unmounts the whole app
 * and the user only sees the dark page background (blank screen).
 */
export default class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("App crashed:", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ padding: 24, color: "#f2f2f2", fontFamily: "system-ui, sans-serif" }}>
        <h1 style={{ fontSize: "1.3rem" }}>Something went wrong</h1>
        <p style={{ opacity: 0.8 }}>Please reload the page. If it keeps happening, report this message:</p>
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 13, opacity: 0.8 }}>{this.state.error.message}</pre>
        <button onClick={() => window.location.reload()} style={{ padding: "10px 16px", marginTop: 12 }}>
          Reload
        </button>
      </div>
    );
  }
}
