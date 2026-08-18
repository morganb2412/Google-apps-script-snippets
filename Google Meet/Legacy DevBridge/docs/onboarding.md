# Onboarding

The path is: install, connect Google, connect GitHub, detect an Apps Script project, create or select a repository, choose a standards preset, and become ready. The extension derives and displays the next step from typed backend onboarding state. Development mode may use explicit local mocks; production never reports a mock connection as successful.

Google connection opens the authorization page in a separate tab and polls onboarding status using an opaque extension session ID. The callback marks that session connected only after state, PKCE, token exchange, verified email, and tenant-domain checks succeed. The GitHub and repository steps remain tracked separately and cannot be presented as live until their adapters are implemented.
