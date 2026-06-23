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

1. Create & activate a virtual environment
2. `pip install -r requirements.txt`
3. Modify `agent.yaml` to desired model
   * See [Pydantic AI](https://pydantic.dev/docs/ai/models/overview/) for details (note: non-OpenAI models will likely require additional `pip install`)
4. Set appropriate environmental variables (e.g., `OPENAI_BASE_URL`, `OPENAI_API_KEY`)
   * For convenience, `python-dotenv` will load from `.env`
4. `python -m streamlit run app.py`
5. In the resulting browser, Yippee Ki‐Yay!!
