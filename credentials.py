from dotenv import load_dotenv
import os
load_dotenv()
gpt4_endpoint = "https://api.openai.com/v1"
gpt4_api_key = os.getenv("OPENAI_KEY")
# this was the version used for the runs (the default as this variable is not used)
gpt4_api_version = "gpt-4o-2024-08-06"