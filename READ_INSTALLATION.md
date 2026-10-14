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
Step 1 — Download & Install Ollama
https://ollama.com/download
https://hubkub.com/how-to/run-llama-4-scout-locally-ollama/

ollama --version

## Step 2 — Download Llama models  
```
    | Model        | Size     | Good For                          |
    |--------------|---------:|-----------------------------------|
    | llama3.2:1b  | ~1 GB    | Very fast, basic tasks            |
    | llama3.2:3b  | ~2 GB    | Good balance, general use         |
    | phi4-mini    | ~2.5 GB  | Smart for its size, reasoning     |
    | gemma3:1b    | ~815 MB  | Smallest usable model             |
    | qwen2.5:3b   | ~2 GB    | Good at coding                    |
```

ollama pull llama4:scout <br>
ollama pull gemma3:1b <br>
ollama pull llama3.2:1b <br>
ollama pull nomic-embed-text:latest <br>

Check installation<br>
ollama list<br>
ollama run gemma3:1b<br>
