import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props { children: ReactNode; section: string }
interface State { failed: boolean }

export class SectionErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("DevBridge section failed", { section: this.props.section, error, info });
  }

  componentDidUpdate(previous: Props) {
    if (previous.section !== this.props.section && this.state.failed) {
      this.setState({ failed: false });
    }
  }

  render() {
    if (this.state.failed) {
      return <div className="notice notice--warning"><strong>This view needs to reload.</strong><p>Select another section and return. DevBridge kept the rest of the toolbar available.</p></div>;
    }
    return this.props.children;
  }
}
