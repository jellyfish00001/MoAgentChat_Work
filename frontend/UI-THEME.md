# W.AgentChat UI Theme

- Themes: `wistron-light` (**default**), `wistron-dark` via `html[data-theme]`.
- Tokens live in `src/app/globals.css`. Prefer `components/ui/*` and semantic classes (`bg-panel`, `bg-accent`, …).
- Do not add `bg-white` / `gray-*` / hard-coded hex in feature screens.
- Accent (企業綠) = CTA / selected / focus only; green buttons use `text-accent-foreground`.
- Light uses frosted, desaturated tokens. Dark stays deep navy.
- ASCII: shark body = lowercase `wistron` letters (slightly translucent); fish `-` ripples stay near full opacity.
- Controls use softer radii; icon buttons `rounded-full`. LangChain mark defaults to icon-only.
- Legacy `wistron-classic` / `wistron` stored values migrate to Light.
