# Architecture standards

- API routes perform validation and delegation, not business logic.
- External providers are accessed through interfaces and adapters.
- The extension is an unprivileged client; sensitive operations remain server-side.
