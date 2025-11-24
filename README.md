This directory contains the first version of all the codes, files, sample data used and the sample results.

Just downloading this directory will not run the code as the Git upload is ignoring my files that store the API Key.

The current directory structure is as:

CampusChallenge-Group-15/
├── .gitignore
├── .env                           ← API key
├── requirements.txt
├── README.md
├── data/
│   └── .csv
├── sample-data/                   ← sample data being used for code testing as full data-set is too large for testing code structure
│   └── API_test.csv
├── prompts/                       ← prompt versions here
│   └── prompt_v1.txt
│   └── prompt_v2.txt                
├── src/
│   ├── api_client.py              ← Groq client + call logic
│   ├── prompt_engine.py           ← loads prompt + builds messages
│   ├── sentiment_analysis.py      ← decision parsing logic (your regex + cleanup)
│   └── run_analysis.py            ← main pipeline runner
└── results/