# usage: python agent.py "AI startups" "climate tech"

import sys
import os
import json
import re
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
from ddgs import DDGS
from jinja2 import Environment, FileSystemLoader

load_dotenv()

client = OpenAI()


def parse_json_response(text: str):
    # strip markdown fences if the model wraps its output
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
    return json.loads(cleaned)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


# step 1 - figure out what sections the newsletter should have
def plan_newsletter(keywords: list[str]) -> list[str]:
    print("\n🔹 Step 1: Planning newsletter structure...")

    system_prompt = (
        "You are a newsletter editor. Given a set of topics/keywords, "
        "plan a newsletter by returning 3-5 section topics. "
        "Return ONLY a JSON array of strings, e.g. "
        '["Topic A", "Topic B", "Topic C"]. No other text.'
    )
    user_prompt = f"Plan a newsletter covering these topics: {', '.join(keywords)}"

    result = call_llm(system_prompt, user_prompt)
    sections = parse_json_response(result)
    print(f"   Planned {len(sections)} sections: {sections}")
    return sections


# step 2 - turn keywords into better search queries
def expand_keywords(keywords: list[str], sections: list[str]) -> list[str]:
    print("\n🔹 Step 2: Expanding keywords into search queries...")

    system_prompt = (
        "You are a research assistant. Given newsletter section topics and "
        "original keywords, generate 1-2 specific web search queries per section "
        "that will find recent, relevant content. "
        "Return ONLY a JSON array of query strings. No other text."
    )
    user_prompt = (
        f"Original keywords: {', '.join(keywords)}\n"
        f"Newsletter sections: {json.dumps(sections)}\n"
        "Generate search queries for each section."
    )

    result = call_llm(system_prompt, user_prompt)
    queries = parse_json_response(result)
    print(f"   Generated {len(queries)} search queries:")
    for q in queries:
        print(f"     - {q}")
    return queries


# step 3 - hit duckduckgo for each query
def search_content(queries: list[str]) -> dict[str, list[dict]]:
    print("\n🔹 Step 3: Searching the web for content...")

    results = {}
    ddgs = DDGS()
    for query in queries:
        try:
            search_results = list(ddgs.text(query, max_results=5))
            results[query] = [
                {
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                }
                for r in search_results
            ]
            print(f"   ✓ '{query}' — {len(search_results)} results")
        except Exception as e:
            print(f"   ✗ '{query}' — search failed: {e}")
            results[query] = []
    return results


# step 4 - let the LLM pick out the good stuff from raw results
def extract_key_info(search_results: dict[str, list[dict]]) -> list[dict]:
    print("\n🔹 Step 4: Extracting key information...")

    system_prompt = (
        "You are a research analyst. Given raw web search results grouped by query, "
        "extract the most relevant and interesting information. "
        "Return a JSON array of objects, each with: "
        '"topic" (string), "key_facts" (array of strings), '
        '"sources" (array of {"title": string, "url": string}). '
        "No other text."
    )
    user_prompt = json.dumps(search_results, indent=2)

    result = call_llm(system_prompt, user_prompt)
    extracted = parse_json_response(result)
    print(f"   Extracted info for {len(extracted)} topics")
    return extracted


# step 5 - write short summaries for each section
def summarize_sections(extracted_info: list[dict]) -> list[dict]:
    print("\n🔹 Step 5: Writing newsletter summaries...")

    system_prompt = (
        "You are a newsletter writer. Given extracted research for each topic, "
        "write a short, engaging newsletter summary paragraph (3-5 sentences) for each. "
        "Return a JSON array of objects with: "
        '"headline" (catchy section title), "summary" (the paragraph), '
        '"sources" (array of {"title": string, "url": string}). '
        "No other text."
    )
    user_prompt = json.dumps(extracted_info, indent=2)

    result = call_llm(system_prompt, user_prompt)
    summaries = parse_json_response(result)
    print(f"   Wrote {len(summaries)} section summaries")
    for s in summaries:
        print(f"     - {s['headline']}")
    return summaries


# step 6 - render everything into the html template
def format_newsletter(sections: list[dict], keywords: list[str]) -> str:
    print("\n🔹 Step 6: Formatting HTML newsletter...")

    template_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("template.html")

    html = template.render(
        title=f"Newsletter: {', '.join(keywords)}",
        date=datetime.now().strftime("%B %d, %Y"),
        tagline=f"Your AI-curated briefing on {', '.join(keywords)}",
        sections=sections,
    )

    output_path = os.path.join(template_dir, "newsletter.html")
    with open(output_path, "w") as f:
        f.write(html)

    print(f"   ✓ Newsletter saved to {output_path}")
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python agent.py \"keyword1\" \"keyword2\" ...")
        print('Example: python agent.py "AI startups" "climate tech"')
        sys.exit(1)

    keywords = sys.argv[1:]
    print("=" * 60)
    print("  AI Newsletter Agent")
    print("=" * 60)
    print(f"Keywords: {', '.join(keywords)}")

    sections = plan_newsletter(keywords)
    queries = expand_keywords(keywords, sections)
    search_results = search_content(queries)
    extracted = extract_key_info(search_results)
    summaries = summarize_sections(extracted)
    output_path = format_newsletter(summaries, keywords)

    print("\n" + "=" * 60)
    print("  Done! Open newsletter.html in your browser.")
    print("=" * 60)


if __name__ == "__main__":
    main()
