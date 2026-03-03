import "dotenv/config";
import express from "express";
import cors from "cors";

import { loadAllActs } from "./loaders/actLoader.js";
import { loadAllQA } from "./loaders/qaLoader.js";
import { askLegalQuestion } from "./pipeline/askLegalQuestion.js";

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json({ limit: "1mb" }));

console.log("🔄 Loading legal datasets...");
const acts = loadAllActs();
const qaData = loadAllQA();
console.log("✅ Legal datasets loaded");


// 🔷 Health Endpoint
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    service: "LegalDoc AI Backend",
    llmMode: process.env.LLM_MODE || "offline"
  });
});


// 🔷 Main Ask Endpoint
app.post("/ask", async (req, res) => {
  try {
    const { query } = req.body;

    if (!query || typeof query !== "string") {
      return res.status(400).json({
        error: "Query must be a valid string"
      });
    }

    const result = await askLegalQuestion(query, acts, qaData);

    res.json(result);

  } catch (error) {
    console.error("❌ Server error:", error.message);

    res.status(500).json({
      error: "Internal server error"
    });
  }
});


app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
});