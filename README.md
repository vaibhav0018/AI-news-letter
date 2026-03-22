# AI Newsletter Generator

Takes a few keywords, searches the web, and spits out a nice HTML newsletter. It runs through 6 steps — planning sections, expanding search queries, searching DuckDuckGo, extracting info, writing summaries, and rendering HTML. Each step uses a separate LLM call so the whole thing works like an agent pipeline.

## Setup

1. Clone and install dependencies:
```bash
git clone https://github.com/vaibhav0018/AI-news-letter.git
cd AI-news-letter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` file with your OpenAI key:
```
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

3. Run it:
```bash
python agent.py "AI startups" "climate tech"
```

4. Open `newsletter.html` in your browser to see the result.

## How it works

- **plan_newsletter** — asks the LLM to decide what sections to include
- **expand_keywords** — generates smarter search queries from your keywords
- **search_content** — hits DuckDuckGo for real results
- **extract_key_info** — LLM pulls out the important bits
- **summarize_sections** — writes short newsletter-style paragraphs
- **format_newsletter** — renders everything into an HTML template

Each step prints progress so you can see the agent working in the terminal.
