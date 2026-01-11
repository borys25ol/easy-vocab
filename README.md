# EasyVocab 🚀

**EasyVocab** is a smart, AI-powered English vocabulary builder designed to streamline the way you learn new words and phrasal verbs. By leveraging the **Google Gemini AI**, it automatically enriches every word you add with translations, usage examples, CEFR levels, and frequency rankings.

## ✨ Key Features

-   **AI-Powered Context**: Automatically generates translations (Ukrainian), informal real-life examples, and synonyms for every entry.
-   **CEFR Leveling**: Intelligent categorization from **A1 to C2** to track your progress and word difficulty.
-   **Frequency Ranking**: Visual badges for word rarity (e.g., *Core 500*, *Active Basic*, *Rare*) using realistic corpus linguistics data.
-   **Phrasal Verb Explorer**: A dedicated module to study phrasal verbs grouped by their root (e.g., *get, take, look, go*).
-   **Interactive Flashcards**: Built-in quiz modes (UA -> EN, EN -> UA) and classic flashcards for active recall.
-   **Audio Pronunciation**: Text-to-speech integration to hear correct English pronunciation.
-   **Clean UI**: Minimalist, mobile-friendly interface with color-coded difficulty borders.

## 🛠️ Tech Stack

-   **Backend**: Python, FastAPI, SQLModel (SQLite).
-   **AI Engine**: Google Gemini Pro (via `google-genai` SDK).
-   **Frontend**: Tailwind CSS, Vanilla JavaScript.
-   **Templating**: Jinja2.

## 🚀 Getting Started

### Prerequisites

-   Python 3.12+
-   Google Gemini API Key (get it at [Google AI Studio](https://aistudio.google.com/))

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/borys25ol/easy-vocab.git
    cd easy-vocab
    ```

2.  **Set up a virtual environment**:
    ```bash
    python -m venv .ve
    source .ve/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Create a `.env` file or export the variable directly:
    ```bash
    export GOOGLE_API_KEY='your_api_key_here'
    ```

### Running the App

Start the FastAPI server using the provided `Makefile` or directly via `uvicorn`:

```bash
# Using Makefile
make runserver

# OR directly
uvicorn main:app --reload
```
