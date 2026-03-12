# How to use docchat

## First time setup

### 1. Clone the repo and install dependencies

```
git clone <your-repo-url>
cd docchat
pip install -r requirements.txt
```

### 2. Get an Anthropic API key

Go to https://console.anthropic.com and create an account if you don't have one.
Once logged in, go to API Keys and generate a new key.

### 3. Set your API key as an environment variable

Mac/Linux — paste this into your terminal:
```
export ANTHROPIC_API_KEY=your-key-here
```

Windows — paste this into Command Prompt:
```
set ANTHROPIC_API_KEY=your-key-here
```

Note: you'll need to do this every time you open a new terminal window unless
you add it to your shell profile (.bashrc, .zshrc, etc.) or a .env file.

### 4. Start the app

```
python app.py
```

Then open your browser and go to http://localhost:5000

---

## Using the app

### Uploading a document

Click the upload area on the left sidebar, or drag and drop a file onto it.
Supported formats are PDF and DOCX. The app will process the file and index
it — this takes a few seconds depending on document length. Once done, the
document will appear in the sidebar and be set as active automatically.

### Asking questions

Type your question in the input box at the bottom and press Enter.
The app searches the document for the most relevant passages, then sends
those passages along with your question to Claude to generate an answer.
Answers are grounded in the document — if something isn't in the document,
it will say so rather than guessing.

Press Shift+Enter if you want a newline in your question instead of sending.

### Switching between documents

Click any document in the left sidebar to switch to it. The chat history
clears when you switch so you start fresh with the new document.

### Removing a document

Hover over a document in the sidebar and click the x button that appears.
This removes it from the database. You can re-upload it later if needed.

### Clearing the chat

Click "Clear chat" in the top right to wipe the conversation history for
the current document. The document stays indexed — you just lose the chat.

---

## Troubleshooting

**"ANTHROPIC_API_KEY is not set"**
You haven't exported your API key in the current terminal session. See step 3 above.

**"Could not extract text from file"**
The file may be a scanned PDF (image-based rather than text-based). The app
can only read PDFs that contain actual text. Try running OCR on the file first,
or copy-paste the content into a DOCX file.

**Answers seem off or incomplete**
This usually means the relevant content is getting split across chunk boundaries
or isn't being retrieved. Try rephrasing your question to be more specific, or
ask about a smaller piece of the document at a time.

**The app is slow on first question after startup**
If sentence-transformers is installed, the model loads on the first request
which takes a few seconds. Subsequent questions will be faster.

**Port 5000 is already in use**
Change the port at the bottom of app.py:
```python
app.run(debug=True, port=5001)
```

---

## Optional: better embeddings

By default the app uses TF-IDF for embeddings, which works fine for most use cases.
If you want higher quality retrieval (especially on longer or more complex documents),
install sentence-transformers:

```
pip install sentence-transformers
```

The app will detect it automatically and use it on next startup. No other changes needed.
