# 🚀 LinkedIn Post: Introducing Synthetic Humans

*(Copy and paste the text below directly into LinkedIn. Attach the 4 screenshots listed at the bottom for maximum engagement and reach.)*

---

Most teams test their web apps using one-shot LLM prompts:
*"Act as a 25-year-old busy professional and tell me if you like this checkout flow."*

The model replies with a polite, superficial paragraph. But real users don’t write polite paragraphs. 

Real users:
❌ Miss buttons hidden below the viewport fold
❌ Get confused by cryptic form validation errors ("Validation Check 4B Failed")
❌ Cycle in circular navigation menus
❌ Experience compounding frustration and abandon your application

To solve this, I built **Synthetic Humans** — an autonomous behavioral simulation and HCI (Human-Computer Interaction) testing platform. 

Instead of generating text opinions, Synthetic Humans instantiates populations of persistent, stateful simulated users that interact with real web applications through headless Playwright browsers.

Here is how it works under the hood:

🧠 **Persistent Cognitive & Affective State**
Synthetic users aren't one-shot prompts. Each agent maintains dynamic mental state across the entire session: working memory of past attempts, visited paths, confidence, and a dynamic **Frustration Gauge**. If an element isn't where an impatient user expects it, frustration spikes until they abandon.

🌐 **Real Headless Browser Execution (Playwright)**
Agents don’t inspect static HTML strings. They run in sandboxed browser contexts with simulated viewports, network conditions, and device profiles—executing real clicks, form typing, and waiting for DOM state transitions.

🔄 **Observe → Decide → Act → Verify Loop**
Simulated users never blindly execute actions. Every step extracts visible DOM affordances, scores candidates based on persona traits (Patience, Technical Proficiency, Risk Tolerance), executes the action, verifies the outcome, and updates cognitive memory.

📊 **Automated Friction & Usability Anomaly Detection**
The analytics engine automatically synthesizes conversion funnels, time-to-completion distributions, and evidence-based UX findings. In our benchmark e-commerce audit:
• Caught an uncommunicated postal code format rejection affecting 25% of simulated users
• Pinpointed an ambiguous CTA ("Review & Finalize Inquiry") placed below the fold that caused 66.7% of beginners to abandon

🎥 **Interactive Trajectory Replay Player**
Review individual sessions just like PostHog or FullStory—with a video-style playback scrubber, step-by-step telemetry, cognitive affective meters, and pulsing target rings showing exactly where each user interacted.

Built with Python 3.12, FastAPI, PostgreSQL/SQLite, Playwright, React, and TypeScript. Includes a headless CLI runner for CI/CD usability regression gates and a provider abstraction supporting OpenAI, Google Gemini, and deterministic local mock engines.

The entire codebase is open-source on GitHub:
👉 https://github.com/yash-aeron/Synthetic-humans

I’d love to hear your thoughts: How does your team currently measure usability and workflow drop-offs before shipping to real users?

---

### 📸 Recommended Image Attachments for LinkedIn (Carousel / Gallery):
1. **`docs/screenshots/interactive_trajectory_player.png`** (Hero slide: shows the interactive video replay player and pulsing click target ring)
2. **`docs/screenshots/completed_experiment_metrics.png`** (Slide 2: shows completion rates, conversion funnel, and discovered usability friction anomalies)
3. **`docs/screenshots/live_experiment_detail.png`** (Slide 3: shows real-time telemetry streaming HUD and active agent workers)
4. **`docs/screenshots/live_dashboard.png`** (Slide 4: shows the experiment management dashboard and research workbench)

---
#ArtificialIntelligence #HCI #AgenticAI #UXDesign #SoftwareTesting #Playwright #ProductManagement #Python #FastAPI #React #FullStackDevelopment
