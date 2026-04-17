# examples

Each folder is an example app.

## cli

Simply demonstrates how to sequence actions and provide a console I/O loop.

To run:

1. Create & activate a virtual environment
2. `pip install -r requirements.txt`
3. `python main.py`

## wj

WaterJug via web-based (Streamlit) interface using LLM for problem configuration.

To run:

2. Create & activate a virtual environment
3. `pip install -r requirements.txt`
4. Create a `secrets.toml` file in `.streamlit` (or can use a global file if preferred); populate an `llm` section with required OpenAI fields (see example below)
5. `python -m streamlit run app.py`
6. In the resulting browser, Yippee Ki‐Yay!!

### Example `secrets.toml`
Used for local access via LM Studio

```
[llm]
base_url="http://localhost:1234/v1"
api_key="not-needed"
```
