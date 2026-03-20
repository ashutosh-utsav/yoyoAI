# Lapel Protocol: Ephemerality Filtering & Anchoring

This is an advanced heuristics approach tailored specifically for lapel microphone data. First, it identifies the staff member and then aggressively filters out "permanent" background colleagues by dropping anyone who speaks across a majority (e.g., >65%) of the audio's duration, retaining only "ephemeral" short-lived customers. Finally, it searches near the customer's identified blocks for specific greeting and farewell keywords by the staff member to perfectly anchor the start and end of the interaction.
