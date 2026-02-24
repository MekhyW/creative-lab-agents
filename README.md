# Trend Scout Agents

Experimental system that scouts live trends and combines them with your personal creative "seeds" from an Obsidian vault to generate unique trend-based content ideas.

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Index your Obsidian Vault:**
   Point the scouter to your markdown notes:
   ```bash
   python vault_ingest.py --vault "C:\Path\To\Your\Vault"
   ```

## Usage

Run the main scouter session:
```bash
python main.py
```

### Flow:
1. **Trend Analysis:** The system scouts trends aligned with your creator identity.
2. **Divergent Brainstorming:** Generates several concepts with unique "twists".
3. **Idea Selection:** You select the best concept to develop.
4. **Script Generation:** Produces draft script variants.
5. **Critique & Approval:** AI-aided refinement and final human approval.

## Configuration

You can customize models and parameters in `config/models.yaml`:
- **name:** OpenAI model to use (e.g., `gpt-4o`, `gpt-4o-mini`).
- **temperature:** Creative randomness (0.0 to 1.0).
- **max_tokens:** Limits for different roles.