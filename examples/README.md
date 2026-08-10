# examples

Each folder provides example apps.

## cli

Simple demonstration of a cogent implementing a console I/O loop, including...
* sensor/actuator integration and runtime arguments (`main`)
* operators leveraging `StagedState`: control logic and flow within an enum (`dp_state`)
* controlled logging (`log_support`)

To run:

1. Create & activate a virtual environment
2. `pip install -r requirements.txt`
3. `python main.py`


## lang

Demonstration of key language features.
* `describe.py`: `FactDescriber` to provide NL descriptions of facts within a kb
* `unit_choice.py`: `EnumClassifier` to select the best enum value (or ``None``) given an NL utterance

To run:

1. Create & activate a virtual environment
2. Modify `main` to desired model and number of trials
   * See [Pydantic AI](https://pydantic.dev/docs/ai/models/overview/) for model details
3. Install additional pydantic groups (e.g., `"pydantic-ai-slim[openai]"`)
4. Set appropriate environmental variables (e.g., `OPENAI_BASE_URL`, `OPENAI_API_KEY`)
   * For convenience, `python-dotenv` will load from `.env`
5. `python <filename>.py`

## web-wj

WaterJug via web-based (Streamlit) interface using an LLM to interpret the problem configuration and a graph-search planner to solve.

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
