# OpenAI API Key Configuration

To use features that rely on the OpenAI API, such as text embeddings or other AI-driven functionalities, you must configure your OpenAI API key.

## Environment Variable Setup

The application expects the OpenAI API key to be available as an environment variable named `OPENAI_API_KEY`.

### Setting the Environment Variable

**Linux/macOS:**

Open your terminal and use the `export` command:

```bash
export OPENAI_API_KEY='your_actual_api_key_here'
```

To make this setting permanent, you can add this line to your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`), and then source the file or open a new terminal session. For example:

```bash
echo "export OPENAI_API_KEY='your_actual_api_key_here'" >> ~/.bashrc
source ~/.bashrc
```

**Windows:**

Using Command Prompt:

```cmd
set OPENAI_API_KEY=your_actual_api_key_here
```

Using PowerShell:

```powershell
$Env:OPENAI_API_KEY = "your_actual_api_key_here"
```

For permanent storage on Windows, you can set it through the System Properties > Environment Variables dialog.

---

**Important:**
- Replace `your_actual_api_key_here` with your actual OpenAI API key.
- Ensure this environment variable is set in the environment where the backend application is run.
- If using `.env` files for local development, you can also add `OPENAI_API_KEY='your_actual_api_key_here'` to your `.env` file, provided the application is configured to load environment variables from such files (e.g., using `python-dotenv`). The `requirements.txt` already includes `python-dotenv`.
