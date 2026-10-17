# installation

    py -3.10 -m pip install torch==2.1.2
    py -3.10 -m pip install transformers==4.37.2
    py -3.10 -m pip show transformers
    py -3.10 -m pip install -U  transformers

    py -3.10 -m pip install numpy==1.26.4
    py -3.10 -m pip install rdflib
    py -3.10 -m pip install pyshacl
    py -3.10 -m pip install bs4
    py -3.10 -m pip install pdfplumber

    py -3.10 -m pip install openai
    py -3.10 -m pip install openpyxl
    py -3.10 -m pip install pdfplumber
    py -3.10 -m pip install chromadb


## Ollama installation
Step 1 - Download & Install Ollama
https://ollama.com/download
https://hubkub.com/how-to/run-llama-4-scout-locally-ollama/

ollama --version

## Step 2 - Download Llama models  

| Model | Size on disk |Developer | Release |
|---|---|---|---|
| Phi-3.5 mini | ~2.2 GB | Microsoft | 20 Aug 2024 |
| Qwen 2.5 | ~1.9 GB |Alibaba | 19 Sep 2024 |
| Llama 3.2 | ~1.3 GB |Meta | 25 Sep 2024 |
| Gemma 3 | ~815 MB | Google | 12 Mar 2025 |

ollama pull phi3.5:3.8b <br>
ollama pull qwen2.5:3b <br>
ollama pull llama3.2:1b <br>
ollama pull gemma3:1b <br>

Check installation<br>
ollama list<br>