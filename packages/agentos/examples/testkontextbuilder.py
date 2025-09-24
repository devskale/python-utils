import json
import sys
import os

# Add the parent directory to sys.path to allow relative imports when running as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kontextBuilder import kontextBuilder

def test_kontextBuilder():
    # Sample data for testing

    # Test the function
    identifier = "Samples@SampleBieter"
    promptid = "PBInfos"
    prompt = kontextBuilder(identifier, promptid, extra_param="value")

    # Check if the prompt contains the expected content
    #print("Prompt preview (first 200 chars):", prompt[:200])

if __name__ == "__main__":
    test_kontextBuilder()
