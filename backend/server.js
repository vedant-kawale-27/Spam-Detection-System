require("dotenv").config();
const express = require("express");
const cors = require("cors");
const axios = require("axios");

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.send("Node backend running ");
});

app.post("/predict", async (req, res) => {
  try {
    const { text, type } = req.body;

    if (!text || !type) {
      return res.status(400).json({ error: "Text and type are required" });
    }

    if (text.length > 5000) {
      return res.status(413).json({
        error: "Text payload exceeds maximum allowed length of 5000 characters",
      });
    }

    const response = await axios.post(process.env.API, {
      text: text,
      type: type,
    });

    res.json(response.data);
  } catch (error) {
    console.error(error.message);
    res.status(500).json({ error: "Something went wrong" });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
