import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export default class AppErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Respectful Meet failed to render:", error, info.componentStack);
  }

  private reload = () => window.location.reload();

  render() {
    if (this.state.hasError) {
      return (
        <main
          role="alert"
          style={{
            minHeight: "100vh",
            display: "grid",
            placeContent: "center",
            gap: 16,
            padding: 24,
            background: "#0e1213",
            color: "#f5ece9",
            textAlign: "center",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <h1 style={{ margin: 0 }}>Respectful Meet</h1>
          <p style={{ color: "#b3a1a1", maxWidth: 420, lineHeight: 1.6 }}>
            The application encountered an error while loading. Please reload the page. If the problem continues, contact support.
          </p>
          <button
            type="button"
            onClick={this.reload}
            style={{
              justifySelf: "center",
              border: 0,
              borderRadius: 10,
              padding: "12px 20px",
              background: "#e0446c",
              color: "#fff",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Reload page
          </button>
        </main>
      );
    }

    return this.props.children;
  }
}
