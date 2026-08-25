const chatWindow = document.getElementById("chat-window");
const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");

function addBubble(text, sender, riskClass = "") {
  const div = document.createElement("div");
  div.className = `bubble ${sender} ${riskClass}`.trim();
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function riskToClass(risk) {
  if (!risk) return "";
  const r = risk.toLowerCase();
  if (r.includes("high")) return "high-risk";
  if (r.includes("suspic")) return "suspicious";
  if (r.includes("safe")) return "safe";
  return "";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  addBubble(message, "user");
  input.value = "";

  const loadingBubble = addBubble("Analyzing message...", "bot");

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || "Something went wrong");

    const lines = [
      `Risk Level: ${data.risk_level}`,
      "",
      "Reasons:",
      ...data.reasons.map((r) => `- ${r}`),
      "",
      "Safety Tips:",
      ...data.safety_tips.map((t) => `- ${t}`),
      "",
      `Suggestion: ${data.suggestions}`,
    ];

    loadingBubble.textContent = lines.join("\n");
    loadingBubble.className = `bubble bot ${riskToClass(data.risk_level)}`;
  } catch (err) {
    loadingBubble.textContent = "Error: " + err.message;
  }
});
