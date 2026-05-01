import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables (only for ElevenLabs key)
load_dotenv()

# Initialize ElevenLabs client
elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# ---------- Ollama configuration ----------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"   # or "llama3", "mistral", etc.

def call_llama2(prompt):
    """Send a prompt to locally running Llama 2 via Ollama."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 3000,      # Changed from 1200 to 3000
            "num_ctx": 8192          # Explicitly use full context window
        }
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json()["response"]

# ---------- AEON essay scraper (robust version) ----------
def get_latest_aeon_essay():
    url = "https://aeon.co/essays"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Try multiple selectors to find the essay link
    article_link = None
    selectors = [
        'a[href*="/essays/"]',
        '.article-card a',
        'a[data-track-content]',
        '.post-preview a',
        'h2 a',
        'article a'
    ]
    for selector in selectors:
        article_link = soup.select_one(selector)
        if article_link and article_link.get('href'):
            break
    
    if not article_link or not article_link.get('href'):
        # Fallback: find any link containing "/essays/"
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            if '/essays/' in link['href']:
                article_link = link
                break
    
    if not article_link:
        raise Exception("Could not find essay link. The website structure may have changed.")
    
    essay_url = article_link['href']
    if not essay_url.startswith('http'):
        essay_url = "https://aeon.co" + essay_url
    
    # Get the essay page
    essay_page = requests.get(essay_url, headers=headers)
    essay_soup = BeautifulSoup(essay_page.text, 'html.parser')
    
    # Get title
    title_selectors = ['h1', '.article-title', 'header h1']
    title = None
    for sel in title_selectors:
        elem = essay_soup.select_one(sel)
        if elem:
            title = elem.get_text(strip=True)
            break
    if not title:
        title = "Untitled Essay"
    
    # Get content
    content_div = None
    content_selectors = [
        'div.article-content',
        'div[data-article-body]',
        'article .content',
        '.article-body',
        'main article'
    ]
    for sel in content_selectors:
        content_div = essay_soup.select_one(sel)
        if content_div:
            break
    
    if not content_div:
        content_div = essay_soup.find('article') or essay_soup.find('main')
    
    paragraphs = content_div.find_all('p') if content_div else essay_soup.find_all('p')
    essay_text = "\n".join([p.get_text() for p in paragraphs[:8]])
    
    return title, essay_url, essay_text

def get_essay_from_url(essay_url):
    """Manual fallback: get essay from a given URL."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(essay_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    title_elem = soup.select_one('h1')
    title = title_elem.get_text(strip=True) if title_elem else "Manual Essay"
    
    content_div = soup.select_one('div.article-content') or soup.select_one('article')
    paragraphs = content_div.find_all('p') if content_div else soup.find_all('p')
    essay_text = "\n".join([p.get_text() for p in paragraphs[:15]])
    
    return title, essay_url, essay_text

# ---------- Podcast script generation ----------
def generate_script(essay_title, essay_text):
    prompt = f"""
You are an expert CAT prep coach. Create a podcast script using the EXACT template below. Replace the placeholders in [brackets] with your content.

---
[INTRO MUSIC]
Host: Welcome to AEON Unpacked for CAT aspirants.

[ESSAY CONTEXT - 2 sentences max, no conclusion]
Host: Today's essay is titled "{essay_title}". [Write 2 sentences about the central theme, without giving away the conclusion.]

[PRIMING QUESTIONS - 3 questions]
Host: As you listen, ask yourself:
1. [Question about main argument]
2. [Question about author's tone]
3. [Question about author's purpose]

---
[READ THE ESSAY WITH VOCABULARY FLAGS]

Now I will read the essay. Each time we encounter a difficult word, you'll hear a [chime] and then a definition.

[Insert the essay text below, but split it into paragraphs. After each difficult word, add:]
[chime]
Host: So, the word "[word]" here means [simple definition in context].
[then continue reading]

[After key paragraphs, add an RC note in italics:]
*Host (as a note to listeners): [e.g., "That was a crucial piece of evidence for the author's claim."]*

---
[POST-READ ANALYSIS]

Host: Now let's break down what we just read.

[SUMMARY - 60 seconds]
Host: In simple terms, [write a concise summary of the main argument and supporting points].

[TONE AND PURPOSE]
Host: The author's tone is [skeptical/persuasive/cautionary/etc.]. Their primary purpose is to [inform/critique/propose/etc.].

---
[CAT-STYLE QUESTIONS]

Host: Let's test your understanding with 3 CAT-style questions.

QUESTION 1 (Main Idea):
[Question stem]
A) [option]
B) [option]
C) [option]
D) [option]

Host: The correct answer is [letter]. Let's discuss why. [Explain reasoning, pointing back to the text]. Option [X] is incorrect because [explain the common mistake].

QUESTION 2 (Inference):
[Question stem]
A) [option]
B) [option]
C) [option]
D) [option]

Host: The correct answer is [letter]. [Explanation].

QUESTION 3 (Detail/Function):
[Question stem]
A) [option]
B) [option]
C) [option]
D) [option]

Host: The correct answer is [letter]. [Explanation].

---
[OUTRO]

Host: Let's recap the vocabulary we learned: [list words and meanings].
Host: Keep thinking critically, and good luck with your CAT prep!

---
Now use the essay text below to fill in the template. Copy the essay text exactly where indicated, but insert [chime] and definitions for at least 5 advanced vocabulary words. Insert at least 2 RC notes in italics after key paragraphs.

Essay Title: {essay_title}

Essay Text:
{essay_text}

Generate the complete script now.
"""
    return call_llama2(prompt)

# ---------- ElevenLabs TTS using your provided method ----------
def script_to_mp3(script, output_filename="podcast_episode.mp3"):
    """Split long scripts, generate audio per chunk, and merge via binary concatenation."""
    print("🎙️ Starting ElevenLabs TTS with chunking...")
    
    # 1. Split the script into chunks (targeting ~4500 chars for safety)
    chunks = split_text(script, 4500)
    print(f"📑 Split into {len(chunks)} chunk(s) for processing.")
    
    temp_files = []
    for i, chunk in enumerate(chunks):
        print(f"  Processing chunk {i+1}/{len(chunks)} (Length: {len(chunk)} chars)...")
        audio_generator = elevenlabs._text_to_speech.convert(
            text=chunk,
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_v3",
            output_format="mp3_44100_128",
        )
        chunk_audio_bytes = b"".join(audio_generator)
        temp_filename = f"_temp_chunk_{i}.mp3"
        with open(temp_filename, "wb") as f:
            f.write(chunk_audio_bytes)
        temp_files.append(temp_filename)
    
    # 2. Merge all chunks by binary concatenation
    print("🔗 Merging audio chunks...")
    with open(output_filename, "wb") as outfile:
        for temp_file in temp_files:
            with open(temp_file, "rb") as infile:
                outfile.write(infile.read())
    
    # 3. Clean up temporary files
    for temp_file in temp_files:
        os.remove(temp_file)
    
    print(f"✅ MP3 saved as {output_filename}")
    return output_filename

def split_text(text, max_chunk_size=4500):
    """Split text at sentence boundaries, respecting the max size."""
    # Split by periods, exclamation, question marks
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if not sentence.strip():
            continue
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

# ---------- Duplicate detection ----------
def already_processed(url):
    if not os.path.exists("last_essay.txt"):
        return False
    with open("last_essay.txt", "r") as f:
        return f.read().strip() == url

# ---------- Main pipeline ----------
def main():
    print("📌 AEON Essay Podcast Builder")
    manual_url = input("Please paste an AEON essay URL (e.g., https://aeon.co/essays/...): ").strip()
    if not manual_url:
        print("No URL provided. Exiting.")
        return
    
    try:
        title, url, essay_text = get_essay_from_url(manual_url)
    except Exception as e:
        print(f"❌ Failed to fetch essay: {e}")
        return
    
    print(f"📄 Essay: {title}\n🔗 {url}")
    
    if already_processed(url):
        print("⏭️ Already processed this essay. Exiting.")
        return
    
    print("🤖 Generating podcast script with Mistral...")
    script = generate_script(title, essay_text)
    
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    print("📝 Script saved to script.txt")
    
    print("🎙️ Converting to speech with ElevenLabs...")
    mp3_file = script_to_mp3(script, f"aeon_{title[:30].replace(' ', '_')}.mp3")
    
    with open("last_essay.txt", "w") as f:
        f.write(url)
    
    print(f"🎉 Done! Your episode is ready: {mp3_file}")

if __name__ == "__main__":
    main()