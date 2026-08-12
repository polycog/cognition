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


## choice

Simple demonstration of a cogent making sequential decisions under constraint, including...
* organization of dynamic sensors/actuators, as well as facilitated reading/invoking (`env`)
* dynamic action proposal (`OperatorGenerator` in `dp` + `main`)
* integrated ranking knowledge (`ActionEvaluator` in `dp` + `main`)

To run:

1. Create & activate a virtual environment
2. `pip install -r requirements.txt`
3. Modify `main` to desired number of trials and ranking knowledge
4. `python main.py`


## lang

Demonstration of key language features.
* `describe.py`: `FactDescriber` to provide NL descriptions of facts within a kb
* `unit_choice.py`: `EnumClassifier` to select the best enum value (or ``None``) given an NL utterance

To run:

1. Create & activate a virtual environment
2. `pip install -r requirements.txt`
3. Modify `main` to desired model and number of trials
   * See [Pydantic AI](https://pydantic.dev/docs/ai/models/overview/) for model details
4. Install additional pydantic groups (e.g., `"pydantic-ai-slim[openai]"`)
5. Set appropriate environmental variables (e.g., `OPENAI_BASE_URL`, `OPENAI_API_KEY`)
   * For convenience, `python-dotenv` will load from `.env`
6. `python <filename>.py`


## chat

Example of multiprocess TUI with a simple cogent bot, including...
* Intent classification (via `EnumClassifier`) -> cogent runtime arguments
* Using the decision process output log (`cogent`) for aggregating a chat response

To run:

1. Create & activate a virtual environment
2. `pip install -r requirements.txt`
3. Modify `agent.yaml` to desired model
   * See [Pydantic AI](https://pydantic.dev/docs/ai/models/overview/) for details
4. Install additional pydantic groups (e.g., `"pydantic-ai-slim[openai]"`)
5. Set appropriate environmental variables (e.g., `OPENAI_BASE_URL`, `OPENAI_API_KEY`)
   * For convenience, `python-dotenv` will load from `.env`
6. Interface-specific (see: `python main.py --help`)
   * In-window: `python main.py`
   * Web: `python main.py --view WEB`
     * For a public URL: `python main.py --view WEB --url <URL>`


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
