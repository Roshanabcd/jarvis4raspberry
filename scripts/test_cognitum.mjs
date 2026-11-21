import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.COGNITUM_API_KEY,
  baseURL: "https://api.cognitum.one/v1",
});

try {
  const res = await client.chat.completions.create({
    model: "cognitum-low",
    max_tokens: 64,
    messages: [{ role: "user", content: "Say hello in one sentence." }],
  });
  console.log(res.choices[0].message.content);
} catch (err) {
  console.error("Cognitum API Response/Error:");
  console.error(err.message || err);
}
