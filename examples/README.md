# examples

Each folder is an example app.

## cli

Simply demonstrates how to sequence actions and provide a console I/O loop.

To run:

1. Create & activate a virtual environment
2. `pip install -r requirements.txt`
3. `python main.py`

## choices

Simple demonstration of the `EnumClassifier` language feature via unit-test framework.

To run:

1. Create & activate a virtual environment
2. Modify `main` to desired model and number of trials-per-test
   * See [Pydantic AI](https://pydantic.dev/docs/ai/models/overview/) for details
3. Install additional pydantic groups (e.g., `"pydantic-ai-slim[openai]"`)
4. Set appropriate environmental variables (e.g., `OPENAI_BASE_URL`, `OPENAI_API_KEY`)
   * For convenience, `python-dotenv` will load from `.env`
5. `python unit_choice.py`

## web-wj

WaterJug via web-based (Streamlit) interface using LLM for problem configuration.

To run:

1. Create & activate a virtual environment
2. `pip install -r requirements.txt`
3. Modify `agent.yaml` to desired model
   * See [Pydantic AI](https://pydantic.dev/docs/ai/models/overview/) for details
4. Install additional pydantic groups (e.g., `"pydantic-ai-slim[openai]"`)
5. Set appropriate environmental variables (e.g., `OPENAI_BASE_URL`, `OPENAI_API_KEY`)
   * For convenience, `python-dotenv` will load from `.env`
6. `python -m streamlit run app.py`
7. In the resulting browser, Yippee Ki‐Yay!!
